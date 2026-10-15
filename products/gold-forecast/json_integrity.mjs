import {createHash} from 'node:crypto';

// Refuse values JSON.stringify silently drops or rewrites. Not authentication
// or canonical JSON; this protects local receipts against serialization aliases.
export function assertLosslessJson(value,path='$',stack=new Set()){
  if(value===null||typeof value==='string'||typeof value==='boolean')return;
  if(typeof value==='number'){
    if(!Number.isFinite(value)||Object.is(value,-0))throw Error('Lossy JSON number at '+path);
    return;
  }
  if(typeof value!=='object')throw Error('Unsupported JSON value at '+path);
  if(stack.has(value))throw Error('Cyclic JSON value at '+path);
  if(Object.getOwnPropertySymbols(value).length)throw Error('Symbol-keyed JSON value at '+path);
  if(!Array.isArray(value)&&![Object.prototype,null].includes(Object.getPrototypeOf(value)))
    throw Error('Non-plain JSON object at '+path);
  stack.add(value);
  try{
    const props=Object.getOwnPropertyDescriptors(value);
    if(Array.isArray(value)){
      for(let i=0;i<value.length;i++){
        const prop=props[String(i)];
        if(!prop||!Object.hasOwn(prop,'value'))throw Error('Sparse/accessor JSON array at '+path+'['+i+']');
        assertLosslessJson(prop.value,path+'['+i+']',stack);
      }
      if(Object.keys(props).some(key=>key!=='length'&&(!/^(0|[1-9]\d*)$/.test(key)||Number(key)>=value.length)))
        throw Error('Extra JSON array property at '+path);
    }else{
      for(const [key,prop] of Object.entries(props)){
        if(!prop.enumerable||!Object.hasOwn(prop,'value'))throw Error('Hidden/accessor JSON property at '+path+'.'+key);
        assertLosslessJson(prop.value,path+'.'+key,stack);
      }
    }
  }finally{stack.delete(value)}
}
export function hash(value){
  assertLosslessJson(value);
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}
