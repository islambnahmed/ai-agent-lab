import readline from 'node:readline';
import {digest, goldPayload, seoPayload} from './canonical.mjs';
for await (const line of readline.createInterface({input:process.stdin,crlfDelay:Infinity})) {
  try {
    const q=JSON.parse(line);
    let v=q.payload;
    if (q.kind==='gold') v=goldPayload(...q.args);
    if (q.kind==='seo') v=seoPayload(...q.args);
    process.stdout.write(JSON.stringify({ok:true, hash:digest(v)})+'\n');
  } catch(e) {process.stdout.write(JSON.stringify({ok:false, error:e.message})+'\n');}
}
