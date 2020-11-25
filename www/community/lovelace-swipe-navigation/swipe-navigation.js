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
return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t})(t)}var A,x,u,E,M,D,
y=0;function f(){if(y<10)try{A=document.querySelector("home-assistant"),x=A.shadowRoot.querySelector("home-assistant-main").shadowRoot,
u=x.querySelector("partial-panel-resolver"),E=x.querySelector("ha-panel-lovelace"),M=E.shadowRoot.querySelector("hui-root"),
D=M.shadowRoot.querySelector("ha-app-layout")}catch(t){y++,setTimeout(function(){return f()},50)}else E&&!M?console.log("hui-root not found."
):E&&!D&&console.log("ha-app-layout not found.")}var I=["APP-HEADER","HA-SLIDER","SWIPE-CARD","HUI-MAP-CARD","ROUND-SLIDER","XIAOMI-VACUUM-MAP-CARD",
"HA-SIDEBAR"];function d(){var o,r,a,t,e,i,l,n,s,c,u,y,f,d,p,h,v,b,m;function w(t){var e,n;0==h&&!l&&m||h==a.length-1&&!l&&!m||("swipe"==i?(e=(
m?"":"-").concat(screen.width/1.5,"px"),n=(m?"-":"").concat(screen.width/1.5,"px"),o.style.transitionDuration="200ms",o.style.opacity=0,
o.style.transform="translate(".concat(e,", 0)"),o.style.transition="transform 0.20s, opacity 0.18s",setTimeout(function(){a[t].dispatchEvent(
new MouseEvent("click",{bubbles:!1,cancelable:!0})),o.style.transitionDuration="0ms",o.style.transform="translate(".concat(n,", 0)"),
o.style.transition="transform 0s"},210),setTimeout(function(){o.style.transitionDuration="200ms",o.style.opacity=1,
o.style.transform="translate(0px, 0)",o.style.transition="transform 0.20s, opacity 0.18s"},250)):"fade"==i?(o.style.transitionDuration="200ms",
o.style.transition="opacity 0.20s",o.style.opacity=0,setTimeout(function(){a[t].dispatchEvent(new MouseEvent("click",{bubbles:!1,cancelable:!0})),
o.style.transitionDuration="0ms",o.style.opacity=0,o.style.transition="opacity 0s"},210),setTimeout(function(){o.style.transitionDuration="200ms",
o.style.transition="opacity 0.20s",o.style.opacity=1},250)):"flip"==i?(o.style.transitionDuration="200ms",o.style.transform="rotatey(90deg)",
o.style.transition="transform 0.20s, opacity 0.20s",o.style.opacity=.25,setTimeout(function(){a[t].dispatchEvent(new MouseEvent("click",{bubbles:!1,
cancelable:!0}))},210),setTimeout(function(){o.style.transitionDuration="200ms",o.style.transform="rotatey(0deg)",
o.style.transition="transform 0.20s, opacity 0.20s",o.style.opacity=1},250)):a[t].dispatchEvent(new MouseEvent("click",{bubbles:!1,cancelable:!0})))}(
E=x.querySelector("ha-panel-lovelace"))&&(M=E.shadowRoot.querySelector("hui-root"))&&(o=(D=M.shadowRoot.querySelector("ha-app-layout")).querySelector(
'[id="view"]'),r=D.querySelector("paper-tabs")||D.querySelector("ha-tabs"),a=r?Array.from(r.querySelectorAll("paper-tab")):[],
t="rtl"==A.style.direction,e=E.lovelace.config.swipe_nav||{},i=null!=e.animate?e.animate:"none",l=null==e.wrap||e.wrap,
n=null!=e.prevent_default&&e.prevent_default,s=null!=e.swipe_amount?e.swipe_amount/Math.pow(10,2):.15,c=null==e.skip_hidden||e.skip_hidden,
u=null!=e.skip_tabs?String(e.skip_tabs).replace(/\s+/g,"").split(",").map(function(t){return parseInt(t,10)}):[],r&&(D.addEventListener("touchstart",
function(t){if("object"==g(t.path)){var e=S(t.path);try{for(e.s();!(n=e.n()).done;){var n=n.value;if("HUI-VIEW"==n.nodeName)break;if(-1<I.indexOf(
n.nodeName))return}}catch(t){e.e(t)}finally{e.f()}}y=t.touches[0].clientX,f=t.touches[0].clientY,b||function(){a=c?a.filter(function(t){
return!u.includes(a.indexOf(t))&&"none"!=getComputedStyle(t,null).display}):a.filter(function(t){return!u.includes(a.indexOf(t))});v=l?0:null,
b=l?a.length-1:null}();h=a.indexOf(r.querySelector(".iron-selected"))},{passive:!0}),D.addEventListener("touchmove",function(t){y&&f&&(
d=y-t.touches[0].clientX,p=f-t.touches[0].clientY,Math.abs(d)>Math.abs(p)&&n&&t.preventDefault())},{passive:!1}),D.addEventListener("touchend",
function(){if(h<0||Math.abs(d)<Math.abs(p))return void(y=f=d=p=null);t&&(d=-d);d>Math.abs(screen.width*s)?(m=!1,h==a.length-1?w(v):w(h+1)
):d<-Math.abs(screen.width*s)&&(m=!0,w(0==h?b:h-1));t&&(m=!m);y=f=d=p=null},{passive:!0}),"swipe"==i&&(D.style.overflow="hidden")))}function p(t){
var e,n=S(t);try{for(n.s();!(e=n.n()).done;){var o=S(e.value.addedNodes);try{for(o.s();!(r=o.n()).done;){var r=r.value;if(
"ha-panel-lovelace"==r.localName)return void new MutationObserver(h).observe(r.shadowRoot,{childList:!0})}}catch(t){o.e(t)}finally{o.f()}}}catch(t){
n.e(t)}finally{n.f()}}function h(t){var e,n=S(t);try{for(n.s();!(e=n.n()).done;){var o=S(e.value.addedNodes);try{for(o.s();!(r=o.n()).done;){
var r=r.value;if("hui-root"==r.localName)return void new MutationObserver(v).observe(r.shadowRoot,{childList:!0})}}catch(t){o.e(t)}finally{o.f()}}
}catch(t){n.e(t)}finally{n.f()}}function v(t){var e,n=S(t);try{for(n.s();!(e=n.n()).done;){var o,r=S(e.value.addedNodes);try{for(r.s();!(o=r.n()
).done;)if("ha-app-layout"==o.value.localName)return void d()}catch(t){r.e(t)}finally{r.f()}}}catch(t){n.e(t)}finally{n.f()}}f(),d(),
new MutationObserver(p).observe(u,{childList:!0});for(var b={header:"%c≡ swipe-navigation".padEnd(27),ver:"%cversion 1.3.2 "},m="%c\n",
w=Math.max.apply(Math,e(Object.values(b).map(function(t){return t.length}))),R=0,O=Object.entries(b);R<O.length;R++){var q=t(O[R],1),k=q[0]
;b[k].length<=w&&(b[k]=b[k].padEnd(w)),"header"==k&&(b[k]="".concat(b[k].slice(0,-1),"⋮ "))}
var j="display:inline-block;border-width:1px 1px 0 1px;border-style:solid;border-color:#424242;color:white;background:#03a9f4;font-size:12px;padding:4px 4.5px 5px 6px;"
,T="border-width:0px 1px 1px 1px;padding:7px;background:white;color:#424242;line-height:0.7;";console.info(b.header+m+b.ver,j,"","".concat(j," "
).concat(T));