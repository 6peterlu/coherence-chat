(this.webpackJsonpweb=this.webpackJsonpweb||[]).push([[0],{104:function(e,t,n){"use strict";n.r(t);var a=n(0),r=n.n(a),c=n(24),s=n.n(c),i=(n(90),n.p,n(91),n(18)),o=n(63),l=n(8),u=n.n(l),d=n(15),j=n(11),h=n(123),b=n(10),m=n(64),x=new(n(26).a);console.log("production");var p="production"==="production".trim()?"https://coherence-chat.herokuapp.com":"http://localhost:5000",O=function(){var e=Object(d.a)(u.a.mark((function e(t,n){var a,r,c,s;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return a=x.get("token"),r={Accept:"application/json","Content-Type":"application/json","Access-Control-Allow_Methods":"POST","Access-Control_Allow_Headers":"*","Access-Control-Allow-Origin":"*"},a&&(r.Authorization="Basic "+btoa(a+":unused")),e.next=5,fetch("".concat(p,"/").concat(t),{method:"post",headers:r,body:JSON.stringify(n)});case 5:if(!(c=e.sent).ok){e.next=11;break}return e.next=9,c.text();case 9:return s=e.sent,e.abrupt("return",JSON.parse(s));case 11:return console.log("POST call to /".concat(t," errored with status ").concat(c.status)),e.abrupt("return",null);case 13:case"end":return e.stop()}}),e)})));return function(t,n){return e.apply(this,arguments)}}(),g=function(){var e=Object(d.a)(u.a.mark((function e(t,n){var a,r,c,s,i;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return a="".concat(p,"/").concat(t),a+="?".concat(m.stringify(n)),r=x.get("token"),c={Accept:"application/json","Access-Control-Allow-Methods":"GET","Access-Control-Allow-Headers":"*","Access-Control-Allow-Origin":"*"},r&&(c.Authorization="Basic "+btoa(r+":unused")),e.next=7,fetch(a,{method:"get",headers:c});case 7:if(!(s=e.sent).ok){e.next=13;break}return e.next=11,s.text();case 11:return i=e.sent,e.abrupt("return",JSON.parse(i));case 13:return console.log("GET call to /".concat(t," errored with status ").concat(s.status)),e.abrupt("return",null);case 15:case"end":return e.stop()}}),e)})));return function(t,n){return e.apply(this,arguments)}}(),f=function(){var e=Object(d.a)(u.a.mark((function e(t,n,a){var r;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,O("login/new",{phoneNumber:t,secretCode:n,password:a});case 2:return r=e.sent,e.abrupt("return",r);case 4:case"end":return e.stop()}}),e)})));return function(t,n,a){return e.apply(this,arguments)}}(),v=function(){var e=Object(d.a)(u.a.mark((function e(t){var n;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,g("patientData/new",{calendarMonth:t});case 2:return n=e.sent,e.abrupt("return",n);case 4:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}(),w=function(){var e=Object(d.a)(u.a.mark((function e(t,n){var a;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,g("patientData/new",{phoneNumber:t,calendarMonth:n});case 2:return a=e.sent,e.abrupt("return",a);case 4:case"end":return e.stop()}}),e)})));return function(t,n){return e.apply(this,arguments)}}(),k=function(){var e=Object(d.a)(u.a.mark((function e(t){var n;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,O("doseWindow/update/new",{updatedDoseWindow:t});case 2:return n=e.sent,e.abrupt("return",n);case 4:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}(),y=function(){var e=Object(d.a)(u.a.mark((function e(){var t;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,O("user/pause/new");case 2:return t=e.sent,e.abrupt("return",t);case 4:case"end":return e.stop()}}),e)})));return function(){return e.apply(this,arguments)}}(),z=function(){var e=Object(d.a)(u.a.mark((function e(){var t;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,O("user/resume/new");case 2:return t=e.sent,e.abrupt("return",t);case 4:case"end":return e.stop()}}),e)})));return function(){return e.apply(this,arguments)}}(),C=n(57),S=n(140),D=n(135),T=n(141),_=n(121),A=n(142),M=n(136),F=n(137),I=n(106),E=n(124),N=n(126),L=n(127),P=n(128),Z=n(129),J=n(9),W=n(2),B=function(e){var t=e.value,n=e.onChangeTime,a=r.a.useState(t.hour),c=Object(j.a)(a,2),s=c[0],i=c[1],o=r.a.useState(t.minute),l=Object(j.a)(o,2),u=l[0],d=l[1];return Object(W.jsxs)(C.a,{direction:"row",children:[Object(W.jsx)(D.a,{options:[1,2,3,4,5,6,7,8,9,10,11,12],value:s>12?s-12:0===s?12:s,plain:!0,onChange:function(e){var t=e.value,a=s>=12?t+12:t%12;i(a),n({hour:a,minute:u})}}),Object(W.jsx)(D.a,{options:["00","15","30","45"],value:"".concat(0===u?"0":"").concat(u.toString()),plain:!0,onChange:function(e){var t=e.value;d(parseInt(t)),n({hour:s,minute:parseInt(t)})}}),Object(W.jsx)(D.a,{options:["AM","PM"],value:s>=12?"PM":"AM",plain:!0,onChange:function(e){var t=e.value,a=s;"AM"===t?s>=12&&(a=s-12,i(s-12)):s<12&&(a=s+12,i(s+12)),n({hour:a,minute:u})}})]})},R=n(80),G=n(122),H=n(79),U=function(e){var t=e.animating,n=Object(R.a)(e,["animating"]);return t?Object(W.jsx)(I.a,Object(i.a)(Object(i.a)({},n),{},{disabled:!0,children:Object(W.jsx)(G.a,{color:Object(H.get)(n,"background.dark",!1)?"#FFF":"brand"})})):Object(W.jsx)(I.a,Object(i.a)(Object(i.a)({},n),{},{children:n.children}))},X=function(){var e=Object(h.a)(["token"]),t=Object(j.a)(e,3),n=t[0],a=(t[1],t[2]),c=r.a.useState(null),s=Object(j.a)(c,2),l=s[0],m=s[1],x=r.a.useState(5),p=Object(j.a)(x,2),O=p[0],g=p[1],f=r.a.useState(null),R=Object(j.a)(f,2),G=R[0],H=R[1],X=r.a.useState(null),q=Object(j.a)(X,2),K=q[0],Q=q[1],V=r.a.useState(null),Y=Object(j.a)(V,2),$=Y[0],ee=Y[1],te=r.a.useState(null),ne=Object(j.a)(te,2),ae=ne[0],re=ne[1],ce=r.a.useState(!1),se=Object(j.a)(ce,2),ie=se[0],oe=se[1],le=[J.DateTime.local(2021,4,1),J.DateTime.local(2021,5,31)],ue=r.a.useCallback(Object(d.a)(u.a.mark((function e(){var t;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(t=null,!K){e.next=7;break}return e.next=4,w(K.value,O);case 4:t=e.sent,e.next=10;break;case 7:return e.next=9,v(O);case 9:t=e.sent;case 10:if(null!==t){e.next=14;break}return a("token"),e.abrupt("return");case 14:m(t),t.impersonateList&&H(t.impersonateList.map((function(e){return{label:e[0],value:e[1]}}))),oe(!1);case 17:case"end":return e.stop()}}),e)}))),[O,K,a]),de=r.a.useMemo((function(){return!!n.token&&(null===l||(l.month!==O||(!!K!==!!l.impersonating||!(!K||!l.impersonating||l.phoneNumber===K.value))))}),[O,n.token,K,l]);r.a.useEffect((function(){console.log("rerendering"),de&&ue()}),[ue,de]);var je=r.a.useCallback((function(e){var t=e.date,n=null,a=J.DateTime.fromJSDate(t),r=a.day;if(null!==l&&l.eventData.length>=r){var c=l.eventData[r-1];a.month===O&&("taken"===c.day_status?n="status-ok":"missed"===c.day_status?n="status-error":"missed"===c.day_status&&(n="status-warning"))}return Object(W.jsx)(C.a,{align:"center",justify:"center",margin:{vertical:"xsmall"},children:Object(W.jsx)(C.a,{width:"30px",height:"30px",round:"medium",background:{color:n},align:"center",justify:"center",children:Object(W.jsx)(S.a,{children:r})})})}),[O,l]),he=r.a.useCallback((function(e){return console.log(e),e.label}),[]),be=function(e){return e.hour<4?e.plus({days:1}):e},me=r.a.useMemo((function(){if(console.log("recomputing"),null===ae)return!0;if(null===l)return!0;var e=be(J.DateTime.utc(2021,5,1,ae.start_hour,ae.start_minute).setZone("local").set({month:5,day:1})),t=be(J.DateTime.utc(2021,5,1,ae.end_hour,ae.end_minute).setZone("local").set({month:5,day:1}));if(t<e.plus({minutes:30}))return!1;var n,a=Object(o.a)(l.doseWindows);try{for(a.s();!(n=a.n()).done;){var r=n.value;if(r.id!==ae.id){var c=be(J.DateTime.utc(2021,5,1,r.start_hour,r.start_minute).setZone("local").set({month:5,day:1})),s=be(J.DateTime.utc(2021,5,1,r.end_hour,r.end_minute).setZone("local").set({month:5,day:1}));if(e<=c&&c<=t)return!1;if(e<=s&&s<=t)return!1}}}catch(i){a.e(i)}finally{a.f()}return!0}),[ae,l]),xe=r.a.useMemo((function(){var e=J.DateTime.local();return e.hour>4&&e.hour<12?"morning":e.hour>12&&e.hour<18?"afternoon":"evening"}),[]),pe=r.a.useMemo((function(){var e=J.DateTime.local();return O===e.month?e:e.set({month:O,day:1})}),[O]),Oe=r.a.useMemo((function(){return(e=["\ud83d\udcab","\ud83c\udf08","\ud83c\udf31","\ud83c\udfc6","\ud83d\udcc8","\ud83d\udc8e","\ud83d\udca1","\ud83d\udd06","\ud83d\udd14"])[Math.floor(e.length*Math.random())];var e}),[]),ge=r.a.useCallback((function(){var e=J.DateTime.utc(2021,5,1,ae.start_hour,ae.start_minute),t=J.DateTime.utc(2021,5,1,ae.end_hour,ae.end_minute);return Object(W.jsxs)(W.Fragment,{children:[Object(W.jsx)(B,{value:e.setZone("local"),color:"dark-3",onChangeTime:function(e){var t=J.DateTime.local(2021,5,1,e.hour,e.minute).setZone("UTC");re(Object(i.a)(Object(i.a)({},ae),{},{start_hour:t.hour,start_minute:t.minute}))}}),Object(W.jsx)(B,{value:t.setZone("local"),color:"dark-3",onChangeTime:function(e){console.log("changed time to ".concat(JSON.stringify(e)));var t=J.DateTime.local(2021,5,1,e.hour,e.minute).setZone("UTC");re(Object(i.a)(Object(i.a)({},ae),{},{end_hour:t.hour,end_minute:t.minute}))}}),Object(W.jsx)(U,{onClick:function(){oe(!0),k(ae),ue(),re(null)},label:me?"Update":"Invalid dose window",disabled:!me,animating:ie})]})}),[ie,ae,ue,me]);return n.token?Object(W.jsxs)(C.a,{children:[null!==G?Object(W.jsxs)(C.a,{direction:"row",align:"center",gap:"small",pad:{horizontal:"medium"},children:[Object(W.jsx)(S.a,{children:"Impersonating:"}),Object(W.jsx)(D.a,{options:G,children:he,onChange:function(e){var t=e.option;console.log("setting"),Q(t)}})]}):null,Object(W.jsx)(C.a,{align:"center",children:Object(W.jsxs)(T.a,{size:"small",children:["Good ",xe,l?", ".concat(l.patientName):"","."]})}),Object(W.jsx)(C.a,{children:l&&l.doseToTakeNow?Object(W.jsx)(C.a,{align:"center",background:{color:"status-warning",dark:!0},round:"medium",margin:{horizontal:"large"},pad:{vertical:"medium"},animation:{type:"pulse",size:"medium",duration:2e3},children:Object(W.jsx)(S.a,{alignSelf:"center",margin:{vertical:"none"},children:"Dose to take now!"})}):Object(W.jsx)(C.a,{align:"center",background:{color:"brand",dark:!0},round:"medium",margin:{horizontal:"large"},children:Object(W.jsxs)(S.a,{children:["No doses to take right now. ",Oe]})})}),Object(W.jsx)(C.a,{margin:{vertical:"medium"},pad:{horizontal:"large"},children:Object(W.jsx)(_.a,{icon:Object(W.jsx)(E.a,{}),label:"How do I use Coherence?",dropContent:Object(W.jsxs)(C.a,{pad:{horizontal:"small"},children:[Object(W.jsx)(S.a,{textAlign:"center",children:"Texting commands"}),Object(W.jsxs)(A.a,{columns:["xsmall","small"],children:[Object(W.jsx)(S.a,{size:"small",children:"T, taken"}),Object(W.jsx)(S.a,{size:"small",children:"Mark your medication as taken at the current time"}),Object(W.jsx)(S.a,{size:"small",children:"T @ 5:00pm"}),Object(W.jsx)(S.a,{size:"small",children:"Mark your medication as taken at 5pm"}),Object(W.jsx)(S.a,{size:"small",children:"S, skip"}),Object(W.jsx)(S.a,{size:"small",children:"Skip the current dose"}),Object(W.jsx)(S.a,{size:"small",children:"1"}),Object(W.jsx)(S.a,{size:"small",children:"Delay the reminder by ten minutes"}),Object(W.jsx)(S.a,{size:"small",children:"2"}),Object(W.jsx)(S.a,{size:"small",children:"Delay the reminder by half an hour"}),Object(W.jsx)(S.a,{size:"small",children:"3"}),Object(W.jsx)(S.a,{size:"small",children:"Delay the reminder by an hour"}),Object(W.jsx)(S.a,{size:"small",children:"20, 20 min"}),Object(W.jsx)(S.a,{size:"small",children:"Delay the reminder by 20 minutes"}),Object(W.jsx)(S.a,{size:"small",children:"W, website, site"}),Object(W.jsx)(S.a,{size:"small",children:"Delay the reminder by 20 minutes"}),Object(W.jsx)(S.a,{size:"small",children:"Eating, going for a walk"}),Object(W.jsx)(S.a,{size:"small",children:"Tell Coherence you're busy with an activity"}),Object(W.jsx)(S.a,{size:"small",children:"X"}),Object(W.jsx)(S.a,{size:"small",children:"Report an error"})]})]}),dropAlign:{top:"bottom"}})}),Object(W.jsxs)(C.a,{pad:"medium",background:{color:"light-3"},children:[Object(W.jsx)(S.a,{textAlign:"center",margin:{vertical:"none"},fill:!0,children:"Medication history"}),Object(W.jsx)(M.a,{date:pe.toISO(),fill:!0,onSelect:function(e){var t=J.DateTime.fromISO(e);ee(t.day)},showAdjacentDays:!1,bounds:le.map((function(e){return e.toString()})),children:je,daysOfWeek:!0,onReference:function(e){g(J.DateTime.fromISO(e).month),m(Object(i.a)(Object(i.a)({},l),{},{eventData:[]}))},animate:!1})]}),$&&Object(W.jsx)(F.a,{onEsc:function(){return ee(!1)},onClickOutside:function(){return ee(!1)},responsive:!1,children:Object(W.jsxs)(C.a,{width:"70vw",pad:"large",children:[Object(W.jsxs)(C.a,{direction:"row",justify:"between",children:[Object(W.jsxs)(S.a,{size:"large",children:[J.DateTime.local().set({month:O}).monthLong," ",$]}),Object(W.jsx)(I.a,{icon:Object(W.jsx)(N.a,{}),onClick:function(){return ee(!1)}})]}),l.eventData[$-1].day_status?Object.keys(l.eventData[$-1].time_of_day).map((function(e){var t=l.eventData[$-1].time_of_day[e][0];return Object(W.jsxs)(W.Fragment,{children:[Object(W.jsxs)(S.a,{margin:{bottom:"none"},children:[e," dose"]},"tod-".concat(e)),Object(W.jsxs)(C.a,{pad:{left:"medium"},direction:"row",align:"center",justify:"between",children:[Object(W.jsxs)(S.a,{size:"small",children:[t.type,t.time?" at ".concat(J.DateTime.fromJSDate(new Date(t.time)).toLocaleString(J.DateTime.TIME_SIMPLE)):""]},"todStatus-".concat(e)),"taken"===t.type?Object(W.jsx)(L.a,{color:"status-ok",size:"small"}):null,"skipped"===t.type?Object(W.jsx)(P.a,{color:"status-warning",size:"small"}):null,"missed"===t.type?Object(W.jsx)(N.a,{color:"status-error",size:"small"}):null]},"todStatusContainer-".concat(e))]})})):Object(W.jsx)(S.a,{children:"No data for this day."})]})}),Object(W.jsxs)(C.a,{align:"center",pad:{vertical:"medium"},margin:{horizontal:"xlarge"},border:"bottom",children:[Object(W.jsx)(S.a,{textAlign:"center",margin:{vertical:"none"},children:"Dose windows"}),l?l.doseWindows.map((function(e){var t=J.DateTime.utc(2021,5,1,e.start_hour,e.start_minute),n=J.DateTime.utc(2021,5,1,e.end_hour,e.end_minute);return Object(W.jsxs)(A.a,{columns:["small","xsmall"],align:"center",pad:{horizontal:"large"},alignContent:"center",justifyContent:"center",justify:"center",children:[Object(W.jsxs)(C.a,{direction:"row",align:"center",children:[Object(W.jsx)(S.a,{children:t.setZone("local").toLocaleString(J.DateTime.TIME_SIMPLE)}),Object(W.jsx)(Z.a,{}),Object(W.jsx)(S.a,{children:n.setZone("local").toLocaleString(J.DateTime.TIME_SIMPLE)})]}),Object(W.jsx)(I.a,{label:"edit",onClick:function(){return re(e)}})]})})):null]}),ae&&Object(W.jsx)(F.a,{onEsc:function(){return re(null)},onClickOutside:function(){return re(null)},responsive:!1,children:Object(W.jsxs)(C.a,{width:"90vw",pad:"large",children:[Object(W.jsxs)(C.a,{direction:"row",justify:"between",children:[Object(W.jsx)(S.a,{size:"large",children:"Edit dose window"}),Object(W.jsx)(I.a,{icon:Object(W.jsx)(N.a,{}),onClick:function(){return re(null)}})]}),Object(W.jsx)(C.a,{children:ge(ae)})]})}),Object(W.jsx)(C.a,{align:"center",pad:{vertical:"medium"},children:l?Object(W.jsxs)(W.Fragment,{children:[Object(W.jsx)(S.a,{textAlign:"center",margin:{vertical:"none"},children:"Pause / resume Coherence"}),Object(W.jsxs)(S.a,{size:"small",color:"dark-3",children:["Coherence is currently ",l.pausedService?"paused":"active","."]}),Object(W.jsxs)(U,{background:l.pausedService?{dark:!0}:null,animating:ie,style:{padding:"10px"},primary:l.pausedService,onClick:Object(d.a)(u.a.mark((function e(){return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(oe(!0),!l.pausedService){e.next=6;break}return e.next=4,z();case 4:e.next=8;break;case 6:return e.next=8,y();case 8:ue();case 9:case"end":return e.stop()}}),e)}))),children:[l.pausedService?"Resume":"Pause"," Coherence"]}),l.pausedService?Object(W.jsx)(S.a,{size:"small",color:"status-warning",textAlign:"center",children:"While Coherence is paused, we can't respond to any texts you send us, or remind you about your medications."}):null]}):null}),Object(W.jsxs)(C.a,{align:"center",pad:{vertical:"medium"},margin:{horizontal:"xlarge"},border:"top",children:[Object(W.jsx)(S.a,{textAlign:"center",margin:{vertical:"none"},children:"Need help with anything?"}),Object(W.jsx)(S.a,{size:"small",color:"dark-3",children:"Our customer service is just a text away at (650) 667-1146. Reach out any time and we'll get back to you in a few hours!"})]}),Object(W.jsx)(C.a,{align:"center",pad:{vertical:"medium"},margin:{horizontal:"xlarge"},border:"top",children:Object(W.jsx)(I.a,{onClick:function(){a("token")},children:"Log out"})})]}):Object(W.jsx)(b.a,{to:"/login"})},q=n(139),K=n(130),Q=n(131),V=n(132),Y=n(133),$=function(){var e=r.a.useState(""),t=Object(j.a)(e,2),n=t[0],a=t[1],c=r.a.useState(""),s=Object(j.a)(c,2),i=s[0],o=s[1],l=r.a.useState(""),m=Object(j.a)(l,2),x=m[0],p=m[1],O=r.a.useState("phoneNumber"),g=Object(j.a)(O,2),v=g[0],w=g[1],k=Object(h.a)(["token"]),y=Object(j.a)(k,2),z=y[0],D=y[1],_=r.a.useState(!1),A=Object(j.a)(_,2),M=A[0],F=A[1],E=r.a.useCallback(Object(d.a)(u.a.mark((function e(){var t;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,f(n,i,x);case 2:null===(t=e.sent)?F(!0):("success"===t.status&&(console.log("setting cookie"),D("token",t.token,{secure:!0})),w(t.status),F(!1));case 4:case"end":return e.stop()}}),e)}))),[x,n,i,D]),N=r.a.useCallback((function(){return"phoneNumber"===v?Object(W.jsxs)(W.Fragment,{children:[Object(W.jsx)(S.a,{textAlign:"center",size:"small",children:"Enter phone number."}),Object(W.jsx)(q.a,{icon:Object(W.jsx)(K.a,{}),placeholder:"(555) 555-5555",size:"small",value:n,onChange:function(e){a(e.target.value)}}),M?Object(W.jsx)(S.a,{size:"small",children:"Invalid phone number."}):null]}):"2fa"===v?Object(W.jsxs)(W.Fragment,{children:[Object(W.jsx)(S.a,{textAlign:"center",size:"small",children:"We've texted you a secret code, enter it below."}),Object(W.jsx)(q.a,{icon:Object(W.jsx)(Q.a,{}),placeholder:"123456",size:"small",value:i,onChange:function(e){o(e.target.value)}}),M?Object(W.jsx)(S.a,{size:"small",children:"Invalid secret code."}):null]}):"password"===v?Object(W.jsxs)(W.Fragment,{children:[Object(W.jsx)(S.a,{textAlign:"center",size:"small",children:"Enter password."}),Object(W.jsx)(q.a,{icon:Object(W.jsx)(V.a,{}),placeholder:"\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022",size:"small",value:x,onChange:function(e){p(e.target.value)},type:"password"}),M?Object(W.jsx)(S.a,{size:"small",children:"Invalid password. If you'd like us to reset it, give us a text at (650) 667-1146."}):null]}):"register"===v?Object(W.jsxs)(W.Fragment,{children:[Object(W.jsx)(S.a,{textAlign:"center",size:"small",children:"Create your password."}),Object(W.jsx)(q.a,{icon:Object(W.jsx)(V.a,{}),placeholder:"\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022",size:"small",value:x,onChange:function(e){p(e.target.value)},type:"password"})]}):void 0}),[M,v,x,n,i]);return z.token?Object(W.jsx)(b.a,{to:"/"}):Object(W.jsxs)(C.a,{height:"100vh",flex:"grow",background:{position:"center",dark:!1,opacity:"strong"},children:[Object(W.jsxs)(C.a,{height:"40vh",align:"center",justify:"center",pad:"large",children:[Object(W.jsx)(S.a,{children:"welcome to"}),Object(W.jsx)(T.a,{children:"coherence"})]}),Object(W.jsxs)(C.a,{height:"60vh",align:"center",justify:"between",background:{color:"brand",dark:!0},pad:"large",children:[Object(W.jsx)(S.a,{color:"white",textAlign:"center",children:"Peace of mind with your medications is just around the corner."}),Object(W.jsxs)(C.a,{children:[Object(W.jsx)(C.a,{width:"200px",margin:{bottom:"medium",top:"xsmall"},children:N()}),Object(W.jsx)(I.a,{label:"submit",icon:Object(W.jsx)(Y.a,{}),onClick:E})]})]})]})},ee=n(38),te=function(){return Object(W.jsx)(ee.a,{children:Object(W.jsxs)(b.d,{children:[Object(W.jsx)(b.b,{exact:!0,path:"/",render:function(){return Object(W.jsx)(X,{})}}),Object(W.jsx)(b.b,{exact:!0,path:"/login",render:function(){return Object(W.jsx)($,{})}})]})})},ne=function(e){e&&e instanceof Function&&n.e(3).then(n.bind(null,143)).then((function(t){var n=t.getCLS,a=t.getFID,r=t.getFCP,c=t.getLCP,s=t.getTTFB;n(e),a(e),r(e),c(e),s(e)}))},ae=n(134),re=n(138);s.a.render(Object(W.jsx)(r.a.StrictMode,{children:Object(W.jsx)(ae.a,{children:Object(W.jsx)(re.a,{theme:{global:{colors:{brand:"#002864",text:{light:"#002864"},paragraph:{light:"#002864"},background:"#FFF"}},spinner:{container:{color:{light:"#002864",dark:"FFF"}}}},themeMode:"light",children:Object(W.jsx)(te,{})})})}),document.getElementById("root")),ne()},90:function(e,t,n){},91:function(e,t,n){}},[[104,1,2]]]);
//# sourceMappingURL=main.43add35c.chunk.js.map