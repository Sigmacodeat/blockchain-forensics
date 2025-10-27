import{f as l}from"./index-BJug7Aun.js";import{j as e}from"./jsx-runtime-DIi0vu7D.js";import{c as u,u as h}from"./createLucideIcon-tprkHvj0.js";import"./index-D73NcUff.js";import"./_commonjsHelpers-CFobbLPQ.js";(function(){try{var r=typeof window<"u"?window:typeof global<"u"?global:typeof globalThis<"u"?globalThis:typeof self<"u"?self:{};r.SENTRY_RELEASE={id:"40e5351344f42b52ea7858082dc1e5478905e644"}}catch{}})();try{(function(){var r=typeof window<"u"?window:typeof global<"u"?global:typeof globalThis<"u"?globalThis:typeof self<"u"?self:{},a=new r.Error().stack;a&&(r._sentryDebugIds=r._sentryDebugIds||{},r._sentryDebugIds[a]="86a38610-4a14-410b-9f2d-26936ddad4fd",r._sentryDebugIdIdentifier="sentry-dbid-86a38610-4a14-410b-9f2d-26936ddad4fd")})()}catch{}/**
 * @license lucide-react v0.307.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const y=u("MapPin",[["path",{d:"M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z",key:"2oe9fu"}],["circle",{cx:"12",cy:"10",r:"3",key:"ilqhr7"}]]);/**
 * @license lucide-react v0.307.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p=u("Search",[["circle",{cx:"11",cy:"11",r:"8",key:"4ej97u"}],["path",{d:"m21 21-4.3-4.3",key:"1qie3q"}]]),m=({searchQuery:r,onSearchQueryChange:a,onSearch:c})=>{const{t:o}=h();return e.jsxs("div",{className:"bg-white dark:bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 transition-all hover:shadow-xl",children:[e.jsxs("h3",{className:"text-base font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white",children:[e.jsx("div",{className:"p-2 bg-primary-100 dark:bg-primary-900/30 rounded-lg",children:e.jsx(p,{className:"h-4 w-4 text-primary-600 dark:text-primary-400"})}),o("investigator.search.title","Address Search")]}),e.jsxs("div",{className:"space-y-3",children:[e.jsxs("div",{className:"relative",children:[e.jsx(p,{className:"absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 dark:text-slate-500"}),e.jsx("input",{type:"text",placeholder:o("investigator.search.placeholder","Enter address (0x... or bc1...)"),className:"w-full pl-10 pr-4 py-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent transition-all text-sm",value:r,onChange:i=>a(i.target.value),onKeyPress:i=>i.key==="Enter"&&c()})]}),e.jsx("button",{onClick:c,className:"w-full bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 dark:from-primary-500 dark:to-primary-600 text-white py-3 px-4 rounded-lg font-medium shadow-lg shadow-primary-500/30 transition-all hover:shadow-xl hover:shadow-primary-500/40 hover:-translate-y-0.5",children:e.jsxs("span",{className:"flex items-center justify-center gap-2",children:[e.jsx(y,{className:"h-4 w-4"}),o("investigator.search.explore","Explore Address")]})})]})]})};m.__docgenInfo={description:"",methods:[],displayName:"AddressSearchPanel",props:{searchQuery:{required:!0,tsType:{name:"string"},description:""},onSearchQueryChange:{required:!0,tsType:{name:"signature",type:"function",raw:"(value: string) => void",signature:{arguments:[{type:{name:"string"},name:"value"}],return:{name:"void"}}},description:""},onSearch:{required:!0,tsType:{name:"signature",type:"function",raw:"() => void",signature:{arguments:[],return:{name:"void"}}},description:""}}};const w={title:"Investigator/AddressSearchPanel",component:m,parameters:{layout:"padded"},tags:["autodocs"],argTypes:{searchQuery:{control:"text"}},args:{onSearchQueryChange:l(),onSearch:l()}},s={args:{searchQuery:""}},t={args:{searchQuery:"0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"}},d={args:{searchQuery:"bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"}},n={args:{searchQuery:"invalid_address_123"}};s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  args: {
    searchQuery: ''
  }
}`,...s.parameters?.docs?.source}}};t.parameters={...t.parameters,docs:{...t.parameters?.docs,source:{originalSource:`{
  args: {
    searchQuery: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'
  }
}`,...t.parameters?.docs?.source}}};d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  args: {
    searchQuery: 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh'
  }
}`,...d.parameters?.docs?.source}}};n.parameters={...n.parameters,docs:{...n.parameters?.docs,source:{originalSource:`{
  args: {
    searchQuery: 'invalid_address_123'
  }
}`,...n.parameters?.docs?.source}}};const k=["Empty","WithEthereumAddress","WithBitcoinAddress","WithInvalidAddress"];export{s as Empty,d as WithBitcoinAddress,t as WithEthereumAddress,n as WithInvalidAddress,k as __namedExportsOrder,w as default};
