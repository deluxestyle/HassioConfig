"use strict";function t(t,e){return r(t)||o(t,e)||s(t,e)||n()}function n(){throw new TypeError(
"Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}
function o(t,e){if("undefined"!=typeof Symbol&&Symbol.iterator in Object(t)){var n=[],o=!0,r=!1,a=void 0;try{for(var i,l=t[Symbol.iterator]();!(o=(
i=l.next()).done)&&(n.push(i.value),!e||n.length!==e);o=!0);}catch(t){r=!0,a=t}finally{try{o||null==l.return||l.return()}finally{if(r)throw a}}
return n}}function r(t){if(Array.isArray(t))return t}function e(t){return l(t)||i(t)||s(t)||a()}function a(){throw new TypeError(
"Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}function i(t){
if("undefined"!=typeof Symbol&&Symbol.iterator in Object(t))return Array.from(t)}function l(t){if(Array.isArray(t))return c(t)}function S(t,e){var n
;if("undefined"==typeof Symbol||null==t[Symbol.iterator]){if(Array.isArray(t)||(n=s(t))||e&&t&&"number"==typeof t.length){n&&(t=n);var o=0,e=function(
){};return{s:e,n:function(){return o>=t.length?{done:!0}:{done:!1,value:t[o++]}},e:function(t){throw t},f:e}}throw new TypeError(
"Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}var r,a=!0,
i=!1;return{s:function(){n=t[Symbol.iterator]()},n:function(){var t=n.next();return a=t.done,t},e:function(t){i=!0,r=t},f:function(){try{
a||null==n.return||n.return()}finally{if(i)throw r}}}}function s(t,e){if(t){if("string"==typeof t)return c(t,e);var n=Object.prototype.toString.call(t
).slice(8,-1);return"Object"===n&&t.constructor&&(n=t.constructor.name),"Map"===n||"Set"===n?Array.from(t
):"Arguments"===n||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)?c(t,e):void 0}}function c(t,e){(null==e||e>t.length)&&(e=t.length);for(var n=0,
o=new Array(e);n<e;n++)o[n]=t[n];return o}function g(t){return(g="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){
return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t})(t)}var A={},x=0
;function E(){if(x<10)try{A.ha=document.querySelector("home-assistant"),A.main=A.ha.shadowRoot.querySelector("home-assistant-main").shadowRoot,
A.panel=A.main.querySelector("partial-panel-resolver"),A.ll=A.main.querySelector("ha-panel-lovelace"),A.root=A.ll.shadowRoot.querySelector("hui-root")
,A.appLayout=A.root.shadowRoot.querySelector("ha-app-layout")}catch(t){x++,setTimeout(function(){return E()},50)}else A.ll&&!A.root?console.log(
"hui-root not found."):A.ll&&!A.appLayout&&console.log("ha-app-layout not found.")}var M=["APP-HEADER","HA-SLIDER","SWIPE-CARD","HUI-MAP-CARD",
"ROUND-SLIDER","XIAOMI-VACUUM-MAP-CARD","HA-SIDEBAR"];function L(){if(document.querySelector("home-assistant").shadowRoot.querySelector(
"home-assistant-main").shadowRoot.querySelector("ha-panel-lovelace")){if(!A.appLayout||!A.appLayout.isConnected)return 0==x?(E(),void L()):void 0
;var o,r,e,n,a,i,l,s,c=A.appLayout.querySelector('[id="view"]'),u=A.appLayout.querySelector("paper-tabs")||A.appLayout.querySelector("ha-tabs"),
y=u?Array.from(u.querySelectorAll("paper-tab")):[],t="rtl"==A.ha.style.direction,f=A.ll.lovelace.config.swipe_nav||{},
p=null!=f.animate?f.animate:"none",d=null==f.wrap||f.wrap,h=null!=f.prevent_default&&f.prevent_default,v=null!=f.swipe_amount?f.swipe_amount/Math.pow(
10,2):.15,m=null==f.skip_hidden||f.skip_hidden,b=null!=f.skip_tabs?String(f.skip_tabs).replace(/\s+/g,"").split(",").map(function(t){return parseInt(t
,10)}):[];u&&(A.appLayout.addEventListener("touchstart",function(t){if("object"==g(t.path)){var e=S(t.path);try{for(e.s();!(n=e.n()).done;){
var n=n.value;if("HUI-VIEW"==n.nodeName)break;if(-1<M.indexOf(n.nodeName))return}}catch(t){e.e(t)}finally{e.f()}}o=t.touches[0].clientX,
r=t.touches[0].clientY,l||(y=m?y.filter(function(t){return!b.includes(y.indexOf(t))&&"none"!=getComputedStyle(t,null).display}):y.filter(function(t){
return!b.includes(y.indexOf(t))}),i=d?0:null,l=d?y.length-1:null);a=y.indexOf(u.querySelector(".iron-selected"))},{passive:!0}),
A.appLayout.addEventListener("touchmove",function(t){o&&r&&(e=o-t.touches[0].clientX,n=r-t.touches[0].clientY,Math.abs(e)>Math.abs(n
)&&h&&t.preventDefault())},{passive:!1}),A.appLayout.addEventListener("touchend",function(){if(a<0||Math.abs(e)<Math.abs(n))return void(o=r=e=n=null)
;t&&(e=-e);e>Math.abs(screen.width*v)?(s=!1,a==y.length-1?w(i):w(a+1)):e<-Math.abs(screen.width*v)&&(s=!0,w(0==a?l:a-1));t&&(s=!s);o=r=e=n=null},{
passive:!0}),"swipe"==p&&(A.appLayout.style.overflow="hidden"))}function w(t){var e,n;0==a&&!d&&s||a==y.length-1&&!d&&!s||("swipe"==p?(e=(s?"":"-"
).concat(screen.width/1.5,"px"),n=(s?"-":"").concat(screen.width/1.5,"px"),c.style.transitionDuration="200ms",c.style.opacity=0,
c.style.transform="translate(".concat(e,", 0)"),c.style.transition="transform 0.20s, opacity 0.18s",setTimeout(function(){y[t].dispatchEvent(
new MouseEvent("click",{bubbles:!1,cancelable:!0})),c.style.transitionDuration="0ms",c.style.transform="translate(".concat(n,", 0)"),
c.style.transition="transform 0s"},210),setTimeout(function(){c.style.transitionDuration="200ms",c.style.opacity=1,
c.style.transform="translate(0px, 0)",c.style.transition="transform 0.20s, opacity 0.18s"},250)):"fade"==p?(c.style.transitionDuration="200ms",
c.style.transition="opacity 0.20s",c.style.opacity=0,setTimeout(function(){y[t].dispatchEvent(new MouseEvent("click",{bubbles:!1,cancelable:!0})),
c.style.transitionDuration="0ms",c.style.opacity=0,c.style.transition="opacity 0s"},210),setTimeout(function(){c.style.transitionDuration="200ms",
c.style.transition="opacity 0.20s",c.style.opacity=1},250)):"flip"==p?(c.style.transitionDuration="200ms",c.style.transform="rotatey(90deg)",
c.style.transition="transform 0.20s, opacity 0.20s",c.style.opacity=.25,setTimeout(function(){y[t].dispatchEvent(new MouseEvent("click",{bubbles:!1,
cancelable:!0}))},210),setTimeout(function(){c.style.transitionDuration="200ms",c.style.transform="rotatey(0deg)",
c.style.transition="transform 0.20s, opacity 0.20s",c.style.opacity=1},250)):y[t].dispatchEvent(new MouseEvent("click",{bubbles:!1,cancelable:!0})))}}
function u(t){var e,n=S(t);try{for(n.s();!(e=n.n()).done;){var o=S(e.value.addedNodes);try{for(o.s();!(r=o.n()).done;){var r=r.value;if(
"ha-panel-lovelace"==r.localName)return void new MutationObserver(y).observe(r.shadowRoot,{childList:!0})}}catch(t){o.e(t)}finally{o.f()}}}catch(t){
n.e(t)}finally{n.f()}}function y(t){var e,n=S(t);try{for(n.s();!(e=n.n()).done;){var o=S(e.value.addedNodes);try{for(o.s();!(r=o.n()).done;){
var r=r.value;if("hui-root"==r.localName)return void new MutationObserver(f).observe(r.shadowRoot,{childList:!0})}}catch(t){o.e(t)}finally{o.f()}}
}catch(t){n.e(t)}finally{n.f()}}function f(t){var e,n=S(t);try{for(n.s();!(e=n.n()).done;){var o,r=S(e.value.addedNodes);try{for(r.s();!(o=r.n()
).done;)if("ha-app-layout"==o.value.localName)return void L()}catch(t){r.e(t)}finally{r.f()}}}catch(t){n.e(t)}finally{n.f()}}E(),x=0,L(),
new MutationObserver(u).observe(A.panel,{childList:!0});for(var p={header:"%c≡ swipe-navigation".padEnd(27),ver:"%cversion 1.3.3 "},d="%c\n",
h=Math.max.apply(Math,e(Object.values(p).map(function(t){return t.length}))),v=0,m=Object.entries(p);v<m.length;v++){var b=t(m[v],1),w=b[0]
;p[w].length<=h&&(p[w]=p[w].padEnd(h)),"header"==w&&(p[w]="".concat(p[w].slice(0,-1),"⋮ "))}
var D="display:inline-block;border-width:1px 1px 0 1px;border-style:solid;border-color:#424242;color:white;background:#03a9f4;font-size:12px;padding:4px 4.5px 5px 6px;"
,I="border-width:0px 1px 1px 1px;padding:7px;background:white;color:#424242;line-height:0.7;";console.info(p.header+d+p.ver,D,"","".concat(D," "
).concat(I));