"use strict";(self.webpackChunkgenoverse=self.webpackChunkgenoverse||[]).push([[129,729],{1398:function(e,n,l){l.r(n);var s=l(1804);n.default={fullscreen:function(){var e=this,n=!0,l="fullscreenchange",s="fullscreenElement",r="requestFullscreen",t="exitFullscreen";document.onmsfullscreenchange||null===document.onmsfullscreenchange?(l="MSFullscreenChange",s="msFullscreenElement",t="msExitFullscreen",r="msRequestFullscreen"):document.body.mozRequestFullScreen?(l="mozfullscreenchange",s="mozFullScreenElement",t="mozCancelFullScreen",r="mozRequestFullScreen"):document.body.webkitRequestFullscreen?(l="webkitfullscreenchange",s="webkitFullscreenElement",t="webkitCancelFullScreen",r="webkitRequestFullscreen"):document.onfullscreenchange||(n=!1),e.fullscreenVars={eventName:l,elemName:s,cancelName:t,requestName:r,enterEvent:function(e){e.preFullscreenWidth=e.superContainer.width(),e.superContainer.addClass("gv-fullscreen"),e.setWidth(window.innerWidth),e.controlPanel.find(".gv-fullscreen-button .fas").removeClass("fa-expand-arrows-alt").addClass("fa-compress-arrows-alt")},exitEvent:function(e){e.superContainer.hasClass("gv-fullscreen")&&(e.superContainer.removeClass("gv-fullscreen"),e.setWidth(e.preFullscreenWidth),e.controlPanel.find(".gv-fullscreen-button .fas").removeClass("fa-compress-arrows-alt").addClass("fa-expand-arrows-alt"))},eventListener:function(){e.superContainer.is(document[e.fullscreenVars.elemName])||(e.fullscreenVars.exitEvent(e),document.removeEventListener(e.fullscreenVars.eventName,e.fullscreenVars.eventListener))}},n&&e.controls.push({icon:'<i class="fas fa-expand-arrows-alt"></i>',class:"gv-fullscreen-button",name:"Toggle fullscreen view",action:function(e){e.superContainer.hasClass("gv-fullscreen")?document[e.fullscreenVars.cancelName]():(document.addEventListener(e.fullscreenVars.eventName,e.fullscreenVars.eventListener),e.superContainer[0][e.fullscreenVars.requestName](),e.fullscreenVars.enterEvent(e))}})},requires:s.default}}}]);
//# sourceMappingURL=129.genoverse.js.map
