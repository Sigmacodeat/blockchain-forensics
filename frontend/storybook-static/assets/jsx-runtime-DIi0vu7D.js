import{b as m}from"./index-D73NcUff.js";(function(){try{var e=typeof window<"u"?window:typeof global<"u"?global:typeof globalThis<"u"?globalThis:typeof self<"u"?self:{};e.SENTRY_RELEASE={id:"40e5351344f42b52ea7858082dc1e5478905e644"}}catch{}})();try{(function(){var e=typeof window<"u"?window:typeof global<"u"?global:typeof globalThis<"u"?globalThis:typeof self<"u"?self:{},n=new e.Error().stack;n&&(e._sentryDebugIds=e._sentryDebugIds||{},e._sentryDebugIds[n]="edbb8988-69e4-4e8e-90d3-8e9cd13ea336",e._sentryDebugIdIdentifier="sentry-dbid-edbb8988-69e4-4e8e-90d3-8e9cd13ea336")})()}catch{}var f={exports:{}},o={};/**
 * @license React
 * react-jsx-runtime.production.min.js
 *
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var p;function x(){if(p)return o;p=1;var e=m(),n=Symbol.for("react.element"),y=Symbol.for("react.fragment"),c=Object.prototype.hasOwnProperty,b=e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner,R={key:!0,ref:!0,__self:!0,__source:!0};function s(i,r,l){var t,u={},d=null,a=null;l!==void 0&&(d=""+l),r.key!==void 0&&(d=""+r.key),r.ref!==void 0&&(a=r.ref);for(t in r)c.call(r,t)&&!R.hasOwnProperty(t)&&(u[t]=r[t]);if(i&&i.defaultProps)for(t in r=i.defaultProps,r)u[t]===void 0&&(u[t]=r[t]);return{$$typeof:n,type:i,key:d,ref:a,props:u,_owner:b.current}}return o.Fragment=y,o.jsx=s,o.jsxs=s,o}var _;function g(){return _||(_=1,f.exports=x()),f.exports}var w=g();export{w as j};
