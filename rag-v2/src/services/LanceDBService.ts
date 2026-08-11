import { connect, Connection, Table } from "@lancedb/lancedb";
import * as path from "path";
import * as fs from "fs"; // Used to check file existence for paths
import { LMStudioRouter } from "./LMStudioRouter"; // For embedding generation

/**
 * Defines the structure for a code role result, representing an AST node or code snippet.
 */
export interface CodeRoleResult {
    id: string; // Unique identifier for the code block (e.g., a hash or UUID)
    role_type: string; // e.g., "function", "class", "interface", "statement"
    filepath: string; // Original file path of the code
    code_content: string; // The actual AST/code snippet content
    symbol_name: string; // The name of the symbol (e.g., function name, class name)
    line_start: number; // Starting line number in the original file
    line_end: number; // Ending line number in the original file
    // Potentially other metadata like "score", "provenance" etc.
    [key: string]: any; // Allow for arbitrary additional properties
}

/**
 * Extends CodeRoleResult with LanceDB-specific search metadata.
 */
export interface LanceDBSearchResult extends CodeRoleResult {
    _distance: number; // Semantic distance from the query vector
}

/**
 * `LanceDBService` encapsulates operations for interacting with a LanceDB vector database.
 * It handles connection, semantic search, and embedding generation via `AIStudioRouter`.
 */
export class LanceDBService {
    private db: Connection | null = null;
    private tableName: string;
    private dbPath: string;
    private embeddingDimension: number;
    private lmStudioRouter: LMStudioRouter;

    /**
     * Constructs a new LanceDBService instance.
     * @param dbPath The file system path where the LanceDB database resides.
     * @param tableName The name of the table to use for storing code vectors (defaults to "mined_code_vectors").
     * @param embeddingDimension The expected dimension of the embeddings (defaults to 768).
     */
    constructor(dbPath: string, tableName: string = "mined_code_vectors", embeddingDimension: number = 1024) {
        this.dbPath = dbPath;
        this.tableName = tableName;
        this.embeddingDimension = embeddingDimension;
        this.lmStudioRouter = LMStudioRouter.getInstance(); // Get the singleton LMStudioRouter
    }

    /**
     * Initializes the connection to the LanceDB database.
     * Throws an error if the connection fails.
     */
    public async init(): Promise<void> {
        if (this.db) {
            console.log("LanceDBService already initialized.");
            return;
        }
        try {
            this.db = await connect(this.dbPath);
            console.log(`Connected to LanceDB at ${this.dbPath}`);
            // In a production setup, the `mined_code_vectors` table would be created
            // and populated by an ingestion pipeline. For this plugin, we assume it exists.
            // A robust check would involve `this.db.tableNames()` and potentially error if missing.
            await this.getOrCreateTable(); // Ensure the table exists (or error if not)
        } catch (error) {
            console.error(`Failed to connect to LanceDB at ${this.dbPath}:`, error);
            throw error;
        }
    }

    /**
     * Attempts to open the LanceDB table. If the table does not exist, it throws an error.
     * In a real ingestion pipeline, this method might also create the table with a specific schema
     * if it detects its absence, potentially with a dummy vector to infer schema.
     * @returns A Promise that resolves to the LanceDB Table object.
     * @throws Error if the service is not initialized or the table does not exist.
     */
    private async getOrCreateTable(): Promise<Table> {
        if (!this.db) {
            throw new Error("LanceDBService not initialized. Call init() first.");
        }
        const tableNames = await this.db.tableNames();
        if (!tableNames.includes(this.tableName)) {
            throw new Error(`LanceDB table '${this.tableName}' does not exist. Please ensure data ingestion has occurred.`);
        }
        return this.db.openTable(this.tableName);
    }

    /**
     * Performs a semantic code search against the LanceDB database.
     * @param queryText The natural language query to search for.
     * @param k The number of nearest neighbors to retrieve (defaults to 5).
     * @returns A Promise resolving to an array of `LanceDBSearchResult` or an empty array if an error occurs.
     */
    public async semanticCodeSearch(queryText: string, k: number = 5): Promise<LanceDBSearchResult[]> {
        if (!this.db) {
            throw new Error("LanceDBService not initialized. Call init() first.");
        }

        try {
            const embedding = await this.lmStudioRouter.generateEmbedding(queryText);
            if (!embedding || embedding.length === 0) {
                console.warn("LanceDBService: Failed to generate embedding for query. Returning empty results.");
                return [];
            }
            if (embedding.length !== this.embeddingDimension) {
                console.warn(`LanceDBService: Embedding dimension mismatch: expected ${this.embeddingDimension}, got ${embedding.length}. ` +
                             `Proceeding, but this might lead to errors if LanceDB requires exact dimensions.`);
            }

            const table = await this.getOrCreateTable();
            // Perform the semantic search, ensuring to fetch all original columns
            const results = await table.query()
                .limit(k)
                .nearestTo(embedding)
                .execute();

            console.log(`LanceDBService: Found ${results.length} semantic results for query: "${queryText.substring(0, 50)}..."`);
            return results as LanceDBSearchResult[];
        } catch (error) {
            console.error(`LanceDBService: Error during LanceDB semantic search for "${queryText.substring(0, 50)}...":`, error);
            return [];
        }
    }

    /**
     * Disconnects from the LanceDB database.
     * Note: The underlying LanceDB Rust/C++ bindings often manage resources internally,
     * so an explicit disconnect might not always be strictly necessary or exposed.
     */
    public async disconnect(): Promise<void> {
        // LanceDB connection managed by underlying Rust/C++ for Node.js.
        // Explicit disconnect might not be directly exposed or needed for `connect` call in many cases,
        // as it might manage resources internally. We'll leave it as a no-op or placeholder for now.
        console.log("LanceDBService: Disconnect called (connection often managed internally by bindings).");
        this.db = null;
    }
}

/**
 * Determines the appropriate LanceDB path based on environment variables or common project structures.
 * This mimics the dynamic path resolution observed in the Python components.
 * @returns The resolved file path for the LanceDB database.
 */
export function getLanceDBPath(): string {
    // 0. Prioritize Canonical Populated Vector Lakehouse Path
    const canonicalPath = "C:\\STUDIES_BACKUP\\Legion-Jacked-Pipeline\\ableton-session-intelligence\\lancedb_web_intel_rag";
    if (fs.existsSync(canonicalPath) && fs.statSync(canonicalPath).isDirectory()) {
        return canonicalPath;
    }

    const defaultDataDir = "lancedb_data"; // Default data directory name
    const lanceDbFileName = "mined_code_vectors.lancedb"; // The LanceDB folder name

    // 1. Prioritize LANCEDB_PATH environment variable
    if (process.env.LANCEDB_PATH) {
        const envPath = process.env.LANCEDB_PATH;
        if (fs.existsSync(envPath) && fs.statSync(envPath).isDirectory()) {
            return envPath;
        }
        console.warn(`LANCEDB_PATH environment variable set to '${envPath}' but path does not exist or is not a directory. Falling back.`);
    }

    // 2. Check a common development path like C:\WEB CASE STUDY\rag-v2\lancedb_data
    const webCaseStudyRoot = "C:\\WEB CASE STUDY";
    const potentialPluginRoot = path.join(webCaseStudyRoot, "rag-v2"); // Assuming plugin is within rag-v2
    const commonLanceDbPath = path.join(potentialPluginRoot, defaultDataDir);

    if (fs.existsSync(commonLanceDbPath) && fs.statSync(commonLanceDbPath).isDirectory()) {
        return commonLanceDbPath;
    }

    // 3. Fallback to a directory relative to the current working directory of the process
    // This is typically where LM Studio might run the plugin script from.
    const cwdLanceDbPath = path.join(process.cwd(), defaultDataDir);
    if (fs.existsSync(cwdLanceDbPath) && fs.statSync(cwdLanceDbPath).isDirectory()) {
        return cwdLanceDbPath;
    }

    // 4. If no existing path found, return a default path that might need to be created.
    // We'll return the common path relative to the plugin's likely root.
    // This path is where data *should* be ingested if not already present.
    console.warn(`No existing LanceDB data directory found. Defaulting to '${commonLanceDbPath}'. Please ensure data ingestion has populated this path.`);
    return commonLanceDbPath;
}