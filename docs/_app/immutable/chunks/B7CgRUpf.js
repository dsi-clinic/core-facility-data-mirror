import{J as i,v as f,U as v,r as u,V as p,W as h,h as d,g as o,A as E,z as T}from"./B9e7qUa4.js";function g(r){var t=document.createElement("template");return t.innerHTML=r,t.content}function n(r,t){var e=u;e.nodes_start===null&&(e.nodes_start=r,e.nodes_end=t)}function x(r,t){var e=(t&p)!==0,_=(t&h)!==0,a,c=!r.startsWith("<!>");return()=>{if(d)return n(o,null),o;a===void 0&&(a=g(c?r:"<!>"+r),e||(a=f(a)));var s=_||v?document.importNode(a,!0):a.cloneNode(!0);if(e){var m=f(s),l=s.lastChild;n(m,l)}else n(s,s);return s}}function M(r=""){if(!d){var t=i(r+"");return n(t,t),t}var e=o;return e.nodeType!==3&&(e.before(e=i()),T(e)),n(e,e),e}function N(){if(d)return n(o,null),o;var r=document.createDocumentFragment(),t=document.createComment(""),e=i();return r.append(t,e),n(t,e),r}function A(r,t){if(d){u.nodes_end=o,E();return}r!==null&&r.before(t)}const y="5";typeof window<"u"&&(window.__svelte||(window.__svelte={v:new Set})).v.add(y);export{A as a,n as b,N as c,M as d,x as t};
