import polars as pl
df = pl.read_parquet(r"C:\WEB CASE STUDY\training_latents\training_index.parquet")
print(df.schema) # Ensure your latent tensor paths are correctly resolved