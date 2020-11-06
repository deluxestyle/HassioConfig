"use strict";function A(t,e){var n;if("undefined"==typeof Symbol||null==t[Symbol.iterator]){if(Array.isArray(t)||(n=s(t)
)||e&&t&&"number"==typeof t.length){n&&(t=n);var o=0,e=function(){};return{s:e,n:function(){return o>=t.length?{done:!0}:{done:!1,value:t[o++]}},
e:function(t){throw t},f:e}}throw new TypeError(
"Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}var r,a=!0,
i=!1;return{s:function(){n=t[Symbol.iterator]()},n:function(){var t=n.next();return a=t.done,t},e:function(t){i=!0,r=t},f:function(){try{
a||null==n.return||n.return()}finally{if(i)throw r}}}}function s(t,e){if(t){if("string"==typeof t)return o(t,e);var n=Object.prototype.toString.call(t
).slice(8,-1);return"Object"===n&&t.constructor&&(n=t.constructor.name),"Map"===n||"Set"===n?Array.from(t
):"Arguments"===n||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)?o(t,e):void 0}}function o(t,e){(null==e||e>t.length)&&(e=t.length);for(var n=0,
o=new Array(e);n<e;n++)o[n]=t[n];return o}function E(t){return(E="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(t){
return typeof t}:function(t){return t&&"function"==typeof Symbol&&t.constructor===Symbol&&t!==Symbol.prototype?"symbol":typeof t})(t)}function g(){
var t,e,o,r,n,a,i,s,l,c,u,y,f,d,p,m,h,v,b,w=document.querySelector("home-assistant");function S(t){var e,n;0==p&&!r&&v||p==b.length-1&&!r&&!v||(
"swipe"==o?(e=(v?"":"-").concat(screen.width/1.5,"px"),n=(v?"-":"").concat(screen.width/1.5,"px"),l.style.transitionDuration="200ms",l.style.opacity=0
,l.style.transform="translate(".concat(e,", 0)"),l.style.transition="transform 0.20s, opacity 0.18s",setTimeout(function(){b[t].dispatchEvent(
new MouseEvent("click",{bubbles:!1,cancelable:!0})),l.style.transitionDuration="0ms",l.style.transform="translate(".concat(n,", 0)"),
l.style.transition="transform 0s"},210),setTimeout(function(){l.style.transitionDuration="200ms",l.style.opacity=1,
l.style.transform="translate(0px, 0)",l.style.transition="transform 0.20s, opacity 0.18s"},250)):"fade"==o?(l.style.transitionDuration="200ms",
l.style.transition="opacity 0.20s",l.style.opacity=0,setTimeout(function(){b[t].dispatchEvent(new MouseEvent("click",{bubbles:!1,cancelable:!0})),
l.style.transitionDuration="0ms",l.style.opacity=0,l.style.transition="opacity 0s"},210),setTimeout(function(){l.style.transitionDuration="200ms",
l.style.transition="opacity 0.20s",l.style.opacity=1},250)):"flip"==o?(l.style.transitionDuration="200ms",l.style.transform="rotatey(90deg)",
l.style.transition="transform 0.20s, opacity 0.20s",l.style.opacity=.25,setTimeout(function(){b[t].dispatchEvent(new MouseEvent("click",{bubbles:!1,
cancelable:!0}))},210),setTimeout(function(){l.style.transitionDuration="200ms",l.style.transform="rotatey(0deg)",
l.style.transition="transform 0.20s, opacity 0.20s",l.style.opacity=1},250)):b[t].dispatchEvent(new MouseEvent("click",{bubbles:!1,cancelable:!0})))}
null!=(w=(w=(w=(w=(w=(w=(w=(w=w&&w.shadowRoot)&&w.querySelector("home-assistant-main"))&&w.shadowRoot)&&w.querySelector(
"app-drawer-layout partial-panel-resolver"))&&w.shadowRoot||w)&&w.querySelector("ha-panel-lovelace"))&&w.shadowRoot)&&w.querySelector("hui-root"))?(
t=w.lovelace.config.swipe_nav||{},
e=w.lovelace.config.custom_header&&w.lovelace.config.custom_header.reverse_tab_direction||"rtl"==document.querySelector("home-assistant"
).style.direction,o=void 0!==t.animate?t.animate:"none",r=void 0===t.wrap||t.wrap,n=void 0!==t.prevent_default&&t.prevent_default,
a=void 0!==t.swipe_amount?t.swipe_amount/Math.pow(10,2):.15,i=void 0===t.skip_hidden||t.skip_hidden,s=void 0!==t.skip_tabs?String(t.skip_tabs
).replace(/\s+/g,"").split(",").map(function(t){return parseInt(t,10)}):[],w=w.shadowRoot.querySelector("ha-app-layout"),l=w.querySelector(
'[id="view"]'),c=w.querySelector("paper-tabs")||w.querySelector("ha-tabs"),b=c?Array.from(c.querySelectorAll("paper-tab")):[],c&&(w.addEventListener(
"touchstart",function(t){var e=["APP-HEADER","HA-SLIDER","SWIPE-CARD","HUI-MAP-CARD","ROUND-SLIDER","XIAOMI-VACUUM-MAP-CARD","HA-SIDEBAR"];if(
"object"==E(t.path)){var n=A(t.path);try{for(n.s();!(o=n.n()).done;){var o=o.value;if("HUI-VIEW"==o.nodeName)break;if(-1<e.indexOf(o.nodeName))return}
}catch(t){n.e(t)}finally{n.f()}}u=t.touches[0].clientX,y=t.touches[0].clientY,h||function(){b=i?b.filter(function(t){return!s.includes(b.indexOf(t)
)&&"none"!=getComputedStyle(t,null).display}):b.filter(function(t){return!s.includes(b.indexOf(t))});m=r?0:null,h=r?b.length-1:null}();p=b.indexOf(
c.querySelector(".iron-selected"))},{passive:!0}),w.addEventListener("touchmove",function(t){u&&y&&(f=u-t.touches[0].clientX,d=y-t.touches[0].clientY,
Math.abs(f)>Math.abs(d)&&n&&t.preventDefault())},{passive:!1}),w.addEventListener("touchend",function(){if(p<0||Math.abs(f)<Math.abs(d))return void(
u=y=f=d=null);e&&(f=-f);f>Math.abs(screen.width*a)?(v=!1,p==b.length-1?S(m):S(p+1)):f<-Math.abs(screen.width*a)&&(v=!0,S(0==p?h:p-1));e&&(v=!v)
;u=y=f=d=null},{passive:!0})),"swipe"==o&&(w.style.overflow="hidden")):setTimeout(g,300)}var t=function(t){t.forEach(function(t){var e,n=A(
t.addedNodes);try{for(n.s();!(e=n.n()).done;)"HA-PANEL-LOVELACE"==e.value.nodeName&&g()}catch(t){n.e(t)}finally{n.f()}})},e=new MutationObserver(t)
;e.observe(document.querySelector("home-assistant").shadowRoot.querySelector("home-assistant-main").shadowRoot.querySelector("partial-panel-resolver")
,{childList:!0}),g();