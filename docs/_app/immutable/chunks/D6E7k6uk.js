import{O as Y,Q as N,R as O,B as H,T as M,y as V,V as b,W as P,X as $,Y as j,Z as T,_ as g,$ as A,a0 as B,k as p,a1 as C,a2 as W,a3 as q,a4 as Q,a5 as X,a6 as Z,a7 as z,g as F,a8 as G,a as J,j as E,a9 as K}from"./c4X_TvN1.js";import{b as U}from"./Co-PfIDx.js";const x=["touchstart","touchmove"];function rr(r){return x.includes(r)}const ar=new Set,D=new Set;function m(r){var S;var a=this,s=a.ownerDocument,c=r.type,o=((S=r.composedPath)==null?void 0:S.call(r))||[],e=o[0]||r.target,d=0,_=r.__root;if(_){var u=o.indexOf(_);if(u!==-1&&(a===document||a===window)){r.__root=a;return}var h=o.indexOf(a);if(h===-1)return;u<=h&&(d=u)}if(e=o[d]||r.target,e!==a){Y(r,"currentTarget",{configurable:!0,get(){return e||s}});var w=M,i=V;N(null),O(null);try{for(var t,n=[];e!==null;){var f=e.assignedSlot||e.parentNode||e.host||null;try{var l=e["__"+c];if(l!==void 0&&(!e.disabled||r.target===e))if(H(l)){var[I,...L]=l;I.apply(e,[r,...L])}else l.call(e,r)}catch(v){t?n.push(v):t=v}if(r.cancelBubble||f===a||f===null)break;e=f}if(t){for(let v of n)queueMicrotask(()=>{throw v});throw t}}finally{r.__root=a,delete r.currentTarget,N(w),O(i)}}}function nr(r,a){var s=a==null?"":typeof a=="object"?a+"":a;s!==(r.__t??(r.__t=r.nodeValue))&&(r.__t=s,r.nodeValue=s+"")}function er(r,a){return k(r,a)}function ir(r,a){b(),a.intro=a.intro??!1;const s=a.target,c=E,o=p;try{for(var e=P(s);e&&(e.nodeType!==8||e.data!==$);)e=j(e);if(!e)throw T;g(!0),A(e),B();const d=k(r,{...a,anchor:e});if(p===null||p.nodeType!==8||p.data!==C)throw W(),T;return g(!1),d}catch(d){if(d===T)return a.recover===!1&&q(),b(),Q(s),g(!1),er(r,a);throw d}finally{g(c),A(o)}}const y=new Map;function k(r,{target:a,anchor:s,props:c={},events:o,context:e,intro:d=!0}){b();var _=new Set,u=i=>{for(var t=0;t<i.length;t++){var n=i[t];if(!_.has(n)){_.add(n);var f=rr(n);a.addEventListener(n,m,{passive:f});var l=y.get(n);l===void 0?(document.addEventListener(n,m,{passive:f}),y.set(n,1)):y.set(n,l+1)}}};u(X(ar)),D.add(u);var h=void 0,w=Z(()=>{var i=s??a.appendChild(z());return F(()=>{if(e){G({});var t=J;t.c=e}o&&(c.$$events=o),E&&U(i,null),h=r(i,c)||{},E&&(V.nodes_end=p),e&&K()}),()=>{var f;for(var t of _){a.removeEventListener(t,m);var n=y.get(t);--n===0?(document.removeEventListener(t,m),y.delete(t)):y.set(t,n)}D.delete(u),i!==s&&((f=i.parentNode)==null||f.removeChild(i))}});return R.set(h,w),h}let R=new WeakMap;function or(r,a){const s=R.get(r);return s?(R.delete(r),s(a)):Promise.resolve()}export{ir as h,er as m,nr as s,or as u};
