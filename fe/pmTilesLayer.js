// via https://medium.com/center-for-coastal-climate-resilience-visualizatio/pmtiles-in-deck-gl-part-i-1ec68814f2da
const { MVTLoader, load } = loaders;
const { MVTLayer } = deck;

export class PMTilesLayer extends MVTLayer {

  constructor(props) {
     super(props)
     this._pmTiles = props.pmTiles
   }

  async getTileData(tile) {
     const { signal } = tile
     const { z, x, y } = tile.index
     const data = await this._pmTiles.getZxy(z, x, y, signal)
     this._pmTiles.getZxyAttempt
     if (!data) {
       return
     }
     if (signal?.aborted) {
       return
     }

     return await load(data.data, MVTLoader)
   }
 }
