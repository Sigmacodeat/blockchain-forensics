import{d as H}from"./index-CLdSGAcA.js";(function(){try{var r=typeof S<"u"?S:typeof E<"u"?E:typeof globalThis<"u"?globalThis:typeof self<"u"?self:{};r.SENTRY_RELEASE={id:"40e5351344f42b52ea7858082dc1e5478905e644"}}catch{}})();try{(function(){var r=typeof S<"u"?S:typeof E<"u"?E:typeof globalThis<"u"?globalThis:typeof self<"u"?self:{},e=new r.Error().stack;e&&(r._sentryDebugIds=r._sentryDebugIds||{},r._sentryDebugIds[e]="0b3bd0cf-fcf5-4200-928f-3831d4bae0f4",r._sentryDebugIdIdentifier="sentry-dbid-0b3bd0cf-fcf5-4200-928f-3831d4bae0f4")})()}catch{}const{useEffect:T,useMemo:_}=__STORYBOOK_MODULE_PREVIEW_API__,{global:E}=__STORYBOOK_MODULE_GLOBAL__,{logger:K}=__STORYBOOK_MODULE_CLIENT_LOGGER__;var g="backgrounds",C={light:{name:"light",value:"#F8F8F8"},dark:{name:"dark",value:"#333"}},{document:u,window:S}=E,D=()=>!!S?.matchMedia("(prefers-reduced-motion: reduce)")?.matches,A=r=>{(Array.isArray(r)?r:[r]).forEach(P)},P=r=>{let e=u.getElementById(r);e&&e.parentElement?.removeChild(e)},z=(r,e)=>{let o=u.getElementById(r);if(o)o.innerHTML!==e&&(o.innerHTML=e);else{let d=u.createElement("style");d.setAttribute("id",r),d.innerHTML=e,u.head.appendChild(d)}},U=(r,e,o)=>{let d=u.getElementById(r);if(d)d.innerHTML!==e&&(d.innerHTML=e);else{let a=u.createElement("style");a.setAttribute("id",r),a.innerHTML=e;let n=`addon-backgrounds-grid${o?`-docs-${o}`:""}`,t=u.getElementById(n);t?t.parentElement?.insertBefore(a,t):u.head.appendChild(a)}},j={cellSize:100,cellAmount:10,opacity:.8},G="addon-backgrounds",R="addon-backgrounds-grid",N=D()?"":"transition: background-color 0.3s;",X=(r,e)=>{let{globals:o,parameters:d,viewMode:a,id:n}=e,{options:t=C,disable:i,grid:l=j}=d[g]||{},p=o[g]||{},c=p.value,f=c?t[c]:void 0,b=f?.value||"transparent",y=p.grid||!1,$=!!f&&!i,h=a==="docs"?`#anchor--${n} .docs-story`:".sb-show-main",O=a==="docs"?`#anchor--${n} .docs-story`:".sb-show-main",Y=d.layout===void 0||d.layout==="padded",L=a==="docs"?20:Y?16:0,{cellAmount:m,cellSize:s,opacity:k,offsetX:x=L,offsetY:v=L}=l,B=a==="docs"?`${G}-docs-${n}`:`${G}-color`,I=a==="docs"?n:null;T(()=>{let M=`
    ${h} {
      background: ${b} !important;
      ${N}
      }`;if(!$){A(B);return}U(B,M,I)},[h,B,I,$,b]);let w=a==="docs"?`${R}-docs-${n}`:`${R}`;return T(()=>{if(!y){A(w);return}let M=[`${s*m}px ${s*m}px`,`${s*m}px ${s*m}px`,`${s}px ${s}px`,`${s}px ${s}px`].join(", "),F=`
        ${O} {
          background-size: ${M} !important;
          background-position: ${x}px ${v}px, ${x}px ${v}px, ${x}px ${v}px, ${x}px ${v}px !important;
          background-blend-mode: difference !important;
          background-image: linear-gradient(rgba(130, 130, 130, ${k}) 1px, transparent 1px),
           linear-gradient(90deg, rgba(130, 130, 130, ${k}) 1px, transparent 1px),
           linear-gradient(rgba(130, 130, 130, ${k/2}) 1px, transparent 1px),
           linear-gradient(90deg, rgba(130, 130, 130, ${k/2}) 1px, transparent 1px) !important;
        }
      `;z(w,F)},[m,s,O,w,y,x,v,k]),r()},W=(r,e=[],o)=>{if(r==="transparent")return"transparent";if(e.find(a=>a.value===r)||r)return r;let d=e.find(a=>a.name===o);if(d)return d.value;if(o){let a=e.map(n=>n.name).join(", ");K.warn(H`
        Backgrounds Addon: could not find the default color "${o}".
        These are the available colors for your story based on your configuration:
        ${a}.
      `)}return"transparent"},q=(r,e)=>{let{globals:o,parameters:d}=e,a=o[g]?.value,n=d[g],t=_(()=>n.disable?"transparent":W(a,n.values,n.default),[n,a]),i=_(()=>t&&t!=="transparent",[t]),l=e.viewMode==="docs"?`#anchor--${e.id} .docs-story`:".sb-show-main",p=_(()=>`
      ${l} {
        background: ${t} !important;
        ${D()?"":"transition: background-color 0.3s;"}
      }
    `,[t,l]);return T(()=>{let c=e.viewMode==="docs"?`addon-backgrounds-docs-${e.id}`:"addon-backgrounds-color";if(!i){A(c);return}U(c,p,e.viewMode==="docs"?e.id:null)},[i,p,e]),r()},J=(r,e)=>{let{globals:o,parameters:d}=e,a=d[g].grid,n=o[g]?.grid===!0&&a.disable!==!0,{cellAmount:t,cellSize:i,opacity:l}=a,p=e.viewMode==="docs",c=d.layout===void 0||d.layout==="padded"?16:0,f=a.offsetX??(p?20:c),b=a.offsetY??(p?20:c),y=_(()=>{let $=e.viewMode==="docs"?`#anchor--${e.id} .docs-story`:".sb-show-main",h=[`${i*t}px ${i*t}px`,`${i*t}px ${i*t}px`,`${i}px ${i}px`,`${i}px ${i}px`].join(", ");return`
      ${$} {
        background-size: ${h} !important;
        background-position: ${f}px ${b}px, ${f}px ${b}px, ${f}px ${b}px, ${f}px ${b}px !important;
        background-blend-mode: difference !important;
        background-image: linear-gradient(rgba(130, 130, 130, ${l}) 1px, transparent 1px),
         linear-gradient(90deg, rgba(130, 130, 130, ${l}) 1px, transparent 1px),
         linear-gradient(rgba(130, 130, 130, ${l/2}) 1px, transparent 1px),
         linear-gradient(90deg, rgba(130, 130, 130, ${l/2}) 1px, transparent 1px) !important;
      }
    `},[i]);return T(()=>{let $=e.viewMode==="docs"?`addon-backgrounds-grid-docs-${e.id}`:"addon-backgrounds-grid";if(!n){A($);return}z($,y)},[n,y,e]),r()},V=globalThis.FEATURES?.backgroundsStoryGlobals?[X]:[J,q],ee={[g]:{grid:{cellSize:20,opacity:.5,cellAmount:5},disable:!1,...!globalThis.FEATURES?.backgroundsStoryGlobals&&{values:Object.values(C)}}},Q={[g]:{value:void 0,grid:!1}},re=globalThis.FEATURES?.backgroundsStoryGlobals?Q:{[g]:null};export{V as decorators,re as initialGlobals,ee as parameters};
