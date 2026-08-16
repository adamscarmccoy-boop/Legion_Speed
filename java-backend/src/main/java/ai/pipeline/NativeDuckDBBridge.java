package ai.pipeline;

public class NativeDuckDBBridge {
    static {
        // Enforce runtime link parameters to load the Colab-built library file
        System.loadLibrary("lance_duckdb_core");
    }

    // Direct entry execution handle linking down to your data rows
    public native String executeVectorPushdownSearch(String promptText);
}
