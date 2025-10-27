import{j as e}from"./jsx-runtime-DIi0vu7D.js";import{c as i,u as c}from"./createLucideIcon-tprkHvj0.js";import"./index-D73NcUff.js";import"./_commonjsHelpers-CFobbLPQ.js";(function(){try{var t=typeof window<"u"?window:typeof global<"u"?global:typeof globalThis<"u"?globalThis:typeof self<"u"?self:{};t.SENTRY_RELEASE={id:"40e5351344f42b52ea7858082dc1e5478905e644"}}catch{}})();try{(function(){var t=typeof window<"u"?window:typeof global<"u"?global:typeof globalThis<"u"?globalThis:typeof self<"u"?self:{},a=new t.Error().stack;a&&(t._sentryDebugIds=t._sentryDebugIds||{},t._sentryDebugIds[a]="a6114547-9eab-4c59-bffd-ad9a5a6b4f78",t._sentryDebugIdIdentifier="sentry-dbid-a6114547-9eab-4c59-bffd-ad9a5a6b4f78")})()}catch{}/**
 * @license lucide-react v0.307.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const x=i("Activity",[["path",{d:"M22 12h-4l-3 9L9 3l-3 9H2",key:"d5dnw9"}]]);/**
 * @license lucide-react v0.307.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h=i("Clock",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["polyline",{points:"12 6 12 12 16 14",key:"68esgv"}]]);/**
 * @license lucide-react v0.307.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const m=i("Route",[["circle",{cx:"6",cy:"19",r:"3",key:"1kj8tv"}],["path",{d:"M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15",key:"1d8sl"}],["circle",{cx:"18",cy:"5",r:"3",key:"gq8acd"}]]);/**
 * @license lucide-react v0.307.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p=i("Users",[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2",key:"1yyitq"}],["circle",{cx:"9",cy:"7",r:"4",key:"nufk8"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87",key:"kshegd"}],["path",{d:"M16 3.13a4 4 0 0 1 0 7.75",key:"1da9ce"}]]),o=({localGraph:t,timelineEvents:a})=>{const{t:d}=c();return e.jsx("div",{className:"mb-8",children:e.jsx("div",{className:"flex items-start justify-between",children:e.jsxs("div",{className:"flex-1",children:[e.jsxs("div",{className:"flex items-center gap-3 mb-3",children:[e.jsx("div",{className:"p-3 bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl shadow-lg",children:e.jsx(m,{className:"h-7 w-7 text-white"})}),e.jsxs("div",{children:[e.jsx("h1",{className:"text-3xl font-bold bg-gradient-to-r from-slate-900 via-primary-800 to-purple-900 dark:from-white dark:via-primary-200 dark:to-purple-200 bg-clip-text text-transparent",children:d("investigator.header.title","Investigator Graph Explorer")}),e.jsx("p",{className:"text-slate-600 dark:text-slate-400 text-sm mt-1",children:d("investigator.header.subtitle","Interaktive Graph-Exploration mit Pfadsuche und Timeline-Analyse")})]})]}),t&&e.jsxs("div",{className:"flex items-center gap-4 mt-4",children:[e.jsx("div",{className:"px-4 py-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700",children:e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx(p,{className:"h-4 w-4 text-primary-600 dark:text-primary-400"}),e.jsx("span",{className:"text-sm font-semibold text-slate-900 dark:text-white",children:Object.keys(t.nodes).length}),e.jsx("span",{className:"text-xs text-slate-500 dark:text-slate-400",children:"Nodes"})]})}),e.jsx("div",{className:"px-4 py-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700",children:e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx(x,{className:"h-4 w-4 text-emerald-600 dark:text-emerald-400"}),e.jsx("span",{className:"text-sm font-semibold text-slate-900 dark:text-white",children:t.links.length}),e.jsx("span",{className:"text-xs text-slate-500 dark:text-slate-400",children:"Connections"})]})}),a&&a.length>0&&e.jsx("div",{className:"px-4 py-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700",children:e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx(h,{className:"h-4 w-4 text-amber-600 dark:text-amber-400"}),e.jsx("span",{className:"text-sm font-semibold text-slate-900 dark:text-white",children:a.length}),e.jsx("span",{className:"text-xs text-slate-500 dark:text-slate-400",children:"Events"})]})})]})]})})})};o.__docgenInfo={description:"",methods:[],displayName:"GraphHeader",props:{localGraph:{required:!0,tsType:{name:"union",raw:"LocalGraph | null",elements:[{name:"LocalGraph"},{name:"null"}]},description:""},timelineEvents:{required:!0,tsType:{name:"Array",elements:[{name:"TimelineEvent"}],raw:"TimelineEvent[]"},description:""}}};const v={title:"Investigator/GraphHeader",component:o,parameters:{layout:"fullscreen"},tags:["autodocs"]},n={args:{localGraph:null,timelineEvents:[]}},s={args:{localGraph:{nodes:{"0xabc":{id:"0xabc",address:"0xabc",chain:"ethereum",taint_score:.5,risk_level:"MEDIUM",labels:["Exchange"],tx_count:10,balance:1.5,first_seen:"2024-01-01",last_seen:"2025-01-15"},"0xdef":{id:"0xdef",address:"0xdef",chain:"ethereum",taint_score:.2,risk_level:"LOW",labels:[],tx_count:5,balance:.8,first_seen:"2024-06-01",last_seen:"2025-01-10"}},links:[{source:"0xabc",target:"0xdef",tx_hash:"0x123",value:1,timestamp:"2025-01-01",event_type:"transaction"}]},timelineEvents:[]}},r={args:{localGraph:{nodes:{"0xabc":{id:"0xabc",address:"0xabc",chain:"ethereum",taint_score:.8,risk_level:"HIGH",labels:["Mixer","High Risk"],tx_count:150,balance:12.5,first_seen:"2023-01-01",last_seen:"2025-01-15"},"0xdef":{id:"0xdef",address:"0xdef",chain:"polygon",taint_score:.3,risk_level:"MEDIUM",labels:["DeFi"],tx_count:75,balance:5.2,first_seen:"2024-01-01",last_seen:"2025-01-12"},"0x789":{id:"0x789",address:"0x789",chain:"ethereum",taint_score:.1,risk_level:"LOW",labels:[],tx_count:25,balance:2.1,first_seen:"2024-08-01",last_seen:"2025-01-08"}},links:[{source:"0xabc",target:"0xdef",tx_hash:"0x123",value:5,timestamp:"2025-01-01",event_type:"transaction"},{source:"0xdef",target:"0x789",tx_hash:"0x456",value:2,timestamp:"2025-01-05",event_type:"transaction"}]},timelineEvents:[{timestamp:"2025-01-01T10:00:00Z",address:"0xabc",event_type:"transfer",value:5,tx_hash:"0x123",risk_score:75},{timestamp:"2025-01-05T14:30:00Z",address:"0xdef",event_type:"swap",value:2,tx_hash:"0x456",risk_score:35},{timestamp:"2025-01-10T08:15:00Z",address:"0x789",event_type:"transfer",value:1,tx_hash:"0x789",risk_score:15}]}},l={args:{localGraph:{nodes:Object.fromEntries(Array.from({length:50},(t,a)=>[`0x${a}`,{id:`0x${a}`,address:`0x${a}`,chain:"ethereum",taint_score:Math.random(),risk_level:["LOW","MEDIUM","HIGH","CRITICAL"][Math.floor(Math.random()*4)],labels:Math.random()>.5?["Label1"]:[],tx_count:Math.floor(Math.random()*1e3),balance:Math.random()*100,first_seen:"2024-01-01",last_seen:"2025-01-15"}])),links:Array.from({length:80},(t,a)=>({source:`0x${Math.floor(Math.random()*50)}`,target:`0x${Math.floor(Math.random()*50)}`,tx_hash:`0x${a}`,value:Math.random()*10,timestamp:"2025-01-01",event_type:"transaction"}))},timelineEvents:Array.from({length:100},(t,a)=>({timestamp:`2025-01-${String(a%30+1).padStart(2,"0")}T10:00:00Z`,address:`0x${Math.floor(Math.random()*50)}`,event_type:["transfer","swap","approval"][Math.floor(Math.random()*3)],value:Math.random()*10,tx_hash:`0x${a}`,risk_score:Math.floor(Math.random()*100)}))}};n.parameters={...n.parameters,docs:{...n.parameters?.docs,source:{originalSource:`{
  args: {
    localGraph: null,
    timelineEvents: []
  }
}`,...n.parameters?.docs?.source}}};s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  args: {
    localGraph: {
      nodes: {
        '0xabc': {
          id: '0xabc',
          address: '0xabc',
          chain: 'ethereum',
          taint_score: 0.5,
          risk_level: 'MEDIUM',
          labels: ['Exchange'],
          tx_count: 10,
          balance: 1.5,
          first_seen: '2024-01-01',
          last_seen: '2025-01-15'
        },
        '0xdef': {
          id: '0xdef',
          address: '0xdef',
          chain: 'ethereum',
          taint_score: 0.2,
          risk_level: 'LOW',
          labels: [],
          tx_count: 5,
          balance: 0.8,
          first_seen: '2024-06-01',
          last_seen: '2025-01-10'
        }
      },
      links: [{
        source: '0xabc',
        target: '0xdef',
        tx_hash: '0x123',
        value: 1,
        timestamp: '2025-01-01',
        event_type: 'transaction'
      }]
    },
    timelineEvents: []
  }
}`,...s.parameters?.docs?.source}}};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
  args: {
    localGraph: {
      nodes: {
        '0xabc': {
          id: '0xabc',
          address: '0xabc',
          chain: 'ethereum',
          taint_score: 0.8,
          risk_level: 'HIGH',
          labels: ['Mixer', 'High Risk'],
          tx_count: 150,
          balance: 12.5,
          first_seen: '2023-01-01',
          last_seen: '2025-01-15'
        },
        '0xdef': {
          id: '0xdef',
          address: '0xdef',
          chain: 'polygon',
          taint_score: 0.3,
          risk_level: 'MEDIUM',
          labels: ['DeFi'],
          tx_count: 75,
          balance: 5.2,
          first_seen: '2024-01-01',
          last_seen: '2025-01-12'
        },
        '0x789': {
          id: '0x789',
          address: '0x789',
          chain: 'ethereum',
          taint_score: 0.1,
          risk_level: 'LOW',
          labels: [],
          tx_count: 25,
          balance: 2.1,
          first_seen: '2024-08-01',
          last_seen: '2025-01-08'
        }
      },
      links: [{
        source: '0xabc',
        target: '0xdef',
        tx_hash: '0x123',
        value: 5,
        timestamp: '2025-01-01',
        event_type: 'transaction'
      }, {
        source: '0xdef',
        target: '0x789',
        tx_hash: '0x456',
        value: 2,
        timestamp: '2025-01-05',
        event_type: 'transaction'
      }]
    },
    timelineEvents: [{
      timestamp: '2025-01-01T10:00:00Z',
      address: '0xabc',
      event_type: 'transfer',
      value: 5,
      tx_hash: '0x123',
      risk_score: 75
    }, {
      timestamp: '2025-01-05T14:30:00Z',
      address: '0xdef',
      event_type: 'swap',
      value: 2,
      tx_hash: '0x456',
      risk_score: 35
    }, {
      timestamp: '2025-01-10T08:15:00Z',
      address: '0x789',
      event_type: 'transfer',
      value: 1,
      tx_hash: '0x789',
      risk_score: 15
    }]
  }
}`,...r.parameters?.docs?.source}}};l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  args: {
    localGraph: {
      nodes: Object.fromEntries(Array.from({
        length: 50
      }, (_, i) => [\`0x\${i}\`, {
        id: \`0x\${i}\`,
        address: \`0x\${i}\`,
        chain: 'ethereum',
        taint_score: Math.random(),
        risk_level: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'][Math.floor(Math.random() * 4)],
        labels: Math.random() > 0.5 ? ['Label1'] : [],
        tx_count: Math.floor(Math.random() * 1000),
        balance: Math.random() * 100,
        first_seen: '2024-01-01',
        last_seen: '2025-01-15'
      }])),
      links: Array.from({
        length: 80
      }, (_, i) => ({
        source: \`0x\${Math.floor(Math.random() * 50)}\`,
        target: \`0x\${Math.floor(Math.random() * 50)}\`,
        tx_hash: \`0x\${i}\`,
        value: Math.random() * 10,
        timestamp: '2025-01-01',
        event_type: 'transaction'
      }))
    },
    timelineEvents: Array.from({
      length: 100
    }, (_, i) => ({
      timestamp: \`2025-01-\${String(i % 30 + 1).padStart(2, '0')}T10:00:00Z\`,
      address: \`0x\${Math.floor(Math.random() * 50)}\`,
      event_type: ['transfer', 'swap', 'approval'][Math.floor(Math.random() * 3)],
      value: Math.random() * 10,
      tx_hash: \`0x\${i}\`,
      risk_score: Math.floor(Math.random() * 100)
    }))
  }
}`,...l.parameters?.docs?.source}}};const g=["Empty","WithGraph","WithGraphAndTimeline","LargeGraph"];export{n as Empty,l as LargeGraph,s as WithGraph,r as WithGraphAndTimeline,g as __namedExportsOrder,v as default};
