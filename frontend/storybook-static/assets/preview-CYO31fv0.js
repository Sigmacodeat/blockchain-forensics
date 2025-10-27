(function(){try{var e=typeof window<"u"?window:typeof d<"u"?d:typeof globalThis<"u"?globalThis:typeof self<"u"?self:{};e.SENTRY_RELEASE={id:"40e5351344f42b52ea7858082dc1e5478905e644"}}catch{}})();try{(function(){var e=typeof window<"u"?window:typeof d<"u"?d:typeof globalThis<"u"?globalThis:typeof self<"u"?self:{},t=new e.Error().stack;t&&(e._sentryDebugIds=e._sentryDebugIds||{},e._sentryDebugIds[t]="31d31892-2cc3-4d22-9dac-fa1196bcdccc",e._sentryDebugIdIdentifier="sentry-dbid-31d31892-2cc3-4d22-9dac-fa1196bcdccc")})()}catch{}const{STORY_CHANGED:r}=__STORYBOOK_MODULE_CORE_EVENTS__,{addons:h}=__STORYBOOK_MODULE_PREVIEW_API__,{global:d}=__STORYBOOK_MODULE_GLOBAL__;var s="storybook/highlight",a="storybookHighlight",f=`${s}/add`,g=`${s}/reset`,{document:o}=d,y=(e="#FF4785",t="dashed")=>`
  outline: 2px ${t} ${e};
  outline-offset: 2px;
  box-shadow: 0 0 0 6px rgba(255,255,255,0.6);
`,i=h.getChannel(),E=e=>{let t=a;l();let _=Array.from(new Set(e.elements)),n=o.createElement("style");n.setAttribute("id",t),n.innerHTML=_.map(c=>`${c}{
          ${y(e.color,e.style)}
         }`).join(" "),o.head.appendChild(n)},l=()=>{let e=a,t=o.getElementById(e);t&&t.parentNode?.removeChild(t)};i.on(r,l);i.on(g,l);i.on(f,E);
