import {forecast} from "./forecast.mjs";

// One calculation per dedicated worker. The UI terminates superseded workers,
// rather than queuing expensive obsolete forecasts on the main thread.
self.onmessage=({data})=>{
  try{
    const {series,horizon,asOf}=data??{};
    const result=forecast(series,horizon,{asOf});
    self.postMessage({ok:true,result});
  }catch(error){
    self.postMessage({ok:false,error:String(error?.message??error)});
  }
};
