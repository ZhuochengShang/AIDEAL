# Alias interfaces

## Proposal batch 1

### AidealAliases0001

- `featureReadType(in: ObjectInput): DataType`  
  Thin wrapper over `Feature.readType`. Requires a `java.io.ObjectInput` positioned at the encoded type.

- `rasterSchemaReadType(in: ObjectInput): DataType`  
  Thin wrapper over `RasterSchemaHelper.readType`. Same input contract as the canonical API.

- `numTilesOf(metadata: RasterMetadata): Int`  
  Thin wrapper returning `metadata.numTiles`.

- `rescaleTo(metadata: RasterMetadata, newRasterWidth: Int, newRasterHeight: Int): RasterMetadata`  
  Thin wrapper over `metadata.rescale(newRasterWidth, newRasterHeight)`.
