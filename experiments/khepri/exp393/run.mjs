import {benchmark} from './provenance_quorum.mjs';
console.log(JSON.stringify({gold:benchmark(),seo:benchmark({seed:394,baseline:100,amplitude:10,faultMultiplier:0.7})},null,2));
