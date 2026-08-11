import * as duckdb from 'duckdb-async';
import { CodeRoleResult } from './LanceDBService'; // Re-use the interface for structured data

/**
 * `DuckDBService` encapsulates operations for interacting with a DuckDB database.
 * It supports in-memory databases or file-backed databases and provides methods
 * for executing SQL queries over structured code metadata.
 */
export class DuckDBService {
    private db: duckdb.Database | null = null;
    private connection: duckdb.Connection | null = null;
    private dbPath: string; // ':memory:' for an in-memory database, or a file path for persistent storage

    /**
     * Constructs a new DuckDBService instance.
     * @param dbPath The path to the DuckDB database file, or ":memory:" for an in-memory database (default).
     */
    constructor(dbPath: string = ":memory:") {
        this.dbPath = dbPath;
    }

    /**
     * Initializes the DuckDB database connection.
     * If using an in-memory database, it also creates a `code_metadata` table for demonstration purposes.
     * Throws an error if the connection or initialization fails.
     */
    public async init(): Promise<void> {
        if (this.db) {
            console.log("DuckDBService already initialized.");
            return;
        }
        try {
            // Check if dbPath is a file or in-memory
            const isMemory = this.dbPath === ":memory:";
            const openMode = isMemory ? undefined : (duckdb as any).OPEN_READONLY;
            
            this.db = openMode ? new duckdb.Database(this.dbPath, openMode) : new duckdb.Database(this.dbPath);
            this.connection = await this.db.connect();
            console.log(`Connected to DuckDB at ${this.dbPath} (Read-Only: ${!isMemory})`);

            if (isMemory) {
                await this.connection.exec(`
                    CREATE TABLE IF NOT EXISTS code_metadata (
                        id VARCHAR,
                        role_type VARCHAR,
                        filepath VARCHAR,
                        symbol_name VARCHAR,
                        line_start INTEGER,
                        line_end INTEGER,
                        code_content VARCHAR
                    );
                `);
                console.log("Ensured 'code_metadata' table exists in in-memory DuckDB.");
            }
        } catch (error) {
            console.error(`Failed to connect or initialize DuckDB at ${this.dbPath}:`, error);
            throw error;
        }
    }

    /**
     * Loads structured code metadata into the `code_metadata` table in DuckDB.
     * This method is primarily for initial data population or demonstration.
     * @param data An array of `CodeRoleResult` objects to insert.
     * @returns A Promise that resolves when all data has been loaded.
     * @throws Error if the service is not initialized.
     */
    public async loadCodeMetadata(data: CodeRoleResult[]): Promise<void> {
        if (!this.connection) {
            throw new Error("DuckDBService not initialized. Call init() first.");
        }
        if (data.length === 0) {
            console.log("No code metadata to load into DuckDB.");
            return;
        }
        // Prepare a statement for efficient batch insertion
        const insertStmt = await this.connection.prepare(`
            INSERT INTO code_metadata (id, role_type, filepath, symbol_name, line_start, line_end, code_content)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        `);
        for (const row of data) {
            await insertStmt.run(
                row.id, row.role_type, row.filepath, row.symbol_name, row.line_start, row.line_end, row.code_content
            );
        }
        await insertStmt.finalize(); // Release the prepared statement
        console.log(`Loaded ${data.length} code metadata entries into DuckDB.`);
    }

    /**
     * Executes a SQL query against the DuckDB database.
     * @param sqlQuery The SQL query string to execute.
     * @returns A Promise resolving to an array of results, typed as `T[]`, or an empty array if an error occurs.
     * @throws Error if the service is not initialized.
     */
    public async duckdbCodeSearch<T>(sqlQuery: string): Promise<T[]> {
        if (!this.connection) {
            throw new Error("DuckDBService not initialized. Call init() first.");
        }
        try {
            // console.log(`Executing DuckDB query: ${sqlQuery}`); // Can be verbose
            const results = await this.connection.all(sqlQuery);
            console.log(`DuckDBService: Query returned ${results.length} results.`);
            return results as T[];
        } catch (error) {
            console.error(`DuckDBService: Error during DuckDB query "${sqlQuery.substring(0, 100)}...":`, error);
            return [];
        }
    }

    /**
     * Disconnects and closes the DuckDB database connection.
     * It's good practice to call this during plugin shutdown to release resources.
     */
    public async disconnect(): Promise<void> {
        if (this.connection) {
            await this.connection.close();
            this.connection = null;
            console.log("DuckDBService: Connection closed.");
        }
        if (this.db) {
            await this.db.close();
            this.db = null;
            console.log("DuckDBService: Database closed.");
        }
    }
}