// common_types.ts

/**
 * Interface for reporting the current status of the Legion backend.
 */
export interface AgentStatus {
    status: string; // e.g., "initializing", "ready", "processing", "error"
    message?: string; // Human-readable status message
    detail?: any; // Optional: More verbose details or current operation data (e.g., error trace)
}

/**
 * Request payload for initiating an audio analysis.
 */
export interface AnalyzeAudioRequest {
    file_path: string; // Absolute path to the audio file to analyze
}

/**
 * Request payload for initiating an audio mastering process.
 */
export interface MasterAudioRequest {
    input_file_path: string; // Absolute path to the input audio file for mastering
    output_file_path?: string; // Optional: Absolute path for the mastered output file. If not provided, a default will be used.
    mastering_config?: any; // Future expansion: detailed mastering parameters (e.g., target_rms, target_crest, specific pedalboard settings)
}

/**
 * Standardized result structure for API operations.
 */
export interface ProcessResult {
    success: boolean; // True if the operation was successful, False otherwise
    message: string; // A human-readable message about the operation's outcome
    data?: any; // Optional: The data returned by the operation (e.g., analysis report, output file path, metrics)
}
