/** Convert a receipt file into a settled outcome without losing failures.
 * No authenticity claims: the caller must separately verify Git anchors.
 */
const HORIZONS=new Set([1,7,30]);
export function evaluateReceiptFile(filename,readText,settle){
  let receipt;
  try{
    receipt=JSON.parse(readText(filename));
    if(!receipt||typeof receipt!=='object'||Array.isArray(receipt))
      throw Error('Invalid receipt object');
    return settle(receipt);
  }catch(e){
    return {
      id:typeof receipt?.id==='string'&&receipt.id?receipt.id:'unreadable-file:'+filename,
      horizon:HORIZONS.has(receipt?.horizon)?receipt.horizon:null,
      status:'quarantined',
      error:e instanceof Error?e.message:String(e)
    };
  }
}
