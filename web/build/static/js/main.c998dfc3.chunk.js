(this.webpackJsonpweb=this.webpackJsonpweb||[]).push([[0],{104:function(e,t,n){"use strict";n.r(t);var a=n(0),r=n.n(a),c=n(24),s=n.n(c),i=(n(90),n(91),n(18)),o=n(63),l=n(8),u=n.n(l),d=n(15),j=n(11),h=n(123),b=n(10),m=n(64),x=new(n(26).a);console.log("production");var p="production"==="production".trim()?"https://coherence-chat.herokuapp.com":"http://localhost:5000",O=function(){var e=Object(d.a)(u.a.mark((function e(t,n){var a,r,c,s;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return a=x.get("token"),r={Accept:"application/json","Content-Type":"application/json","Access-Control-Allow_Methods":"POST","Access-Control_Allow_Headers":"*","Access-Control-Allow-Origin":"*"},a&&(r.Authorization="Basic "+btoa(a+":unused")),e.next=5,fetch("".concat(p,"/").concat(t),{method:"post",headers:r,body:JSON.stringify(n)});case 5:if(!(c=e.sent).ok){e.next=11;break}return e.next=9,c.text();case 9:return s=e.sent,e.abrupt("return",JSON.parse(s));case 11:return console.log("POST call to /".concat(t," errored with status ").concat(c.status)),e.abrupt("return",null);case 13:case"end":return e.stop()}}),e)})));return function(t,n){return e.apply(this,arguments)}}(),g=function(){var e=Object(d.a)(u.a.mark((function e(t,n){var a,r,c,s,i;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return a="".concat(p,"/").concat(t),a+="?".concat(m.stringify(n)),r=x.get("token"),c={Accept:"application/json","Access-Control-Allow-Methods":"GET","Access-Control-Allow-Headers":"*","Access-Control-Allow-Origin":"*"},r&&(c.Authorization="Basic "+btoa(r+":unused")),e.next=7,fetch(a,{method:"get",headers:c});case 7:if(!(s=e.sent).ok){e.next=13;break}return e.next=11,s.text();case 11:return i=e.sent,e.abrupt("return",JSON.parse(i));case 13:return console.log("GET call to /".concat(t," errored with status ").concat(s.status)),e.abrupt("return",null);case 15:case"end":return e.stop()}}),e)})));return function(t,n){return e.apply(this,arguments)}}(),f=function(){var e=Object(d.a)(u.a.mark((function e(t,n,a){var r;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,O("login/new",{phoneNumber:t,secretCode:n,password:a});case 2:return r=e.sent,e.abrupt("return",r);case 4:case"end":return e.stop()}}),e)})));return function(t,n,a){return e.apply(this,arguments)}}(),v=function(){var e=Object(d.a)(u.a.mark((function e(t){var n;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,g("patientData/new",{calendarMonth:t});case 2:return n=e.sent,e.abrupt("return",n);case 4:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}(),w=function(){var e=Object(d.a)(u.a.mark((function e(t,n){var a;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,g("patientData/new",{phoneNumber:t,calendarMonth:n});case 2:return a=e.sent,e.abrupt("return",a);case 4:case"end":return e.stop()}}),e)})));return function(t,n){return e.apply(this,arguments)}}(),k=function(){var e=Object(d.a)(u.a.mark((function e(t){var n;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,O("doseWindow/update/new",{updatedDoseWindow:t});case 2:return n=e.sent,e.abrupt("return",n);case 4:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}(),y=function(){var e=Object(d.a)(u.a.mark((function e(){var t;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,O("user/pause/new");case 2:return t=e.sent,e.abrupt("return",t);case 4:case"end":return e.stop()}}),e)})));return function(){return e.apply(this,arguments)}}(),z=function(){var e=Object(d.a)(u.a.mark((function e(){var t;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,O("user/resume/new");case 2:return t=e.sent,e.abrupt("return",t);case 4:case"end":return e.stop()}}),e)})));return function(){return e.apply(this,arguments)}}(),C=n(57),S=n(140),T=n(135),D=n(141),_=n(121),A=n(142),M=n(136),F=n(137),I=n(106),E=n(124),N=n(126),P=n(127),L=n(128),Z=n(129),W=n(9),J=n(2),B=function(e){var t=e.value,n=e.onChangeTime,a=r.a.useState(t.hour),c=Object(j.a)(a,2),s=c[0],i=c[1],o=r.a.useState(t.minute),l=Object(j.a)(o,2),u=l[0],d=l[1];return Object(J.jsxs)(C.a,{direction:"row",children:[Object(J.jsx)(T.a,{options:[1,2,3,4,5,6,7,8,9,10,11,12],value:s>12?s-12:0===s?12:s,plain:!0,onChange:function(e){var t=e.value,a=s>=12?t+12:t%12;i(a),n({hour:a,minute:u})}}),Object(J.jsx)(T.a,{options:["00","15","30","45"],value:"".concat(0===u?"0":"").concat(u.toString()),plain:!0,onChange:function(e){var t=e.value;d(parseInt(t)),n({hour:s,minute:parseInt(t)})}}),Object(J.jsx)(T.a,{options:["AM","PM"],value:s>=12?"PM":"AM",plain:!0,onChange:function(e){var t=e.value,a=s;"AM"===t?s>=12&&(a=s-12,i(s-12)):s<12&&(a=s+12,i(s+12)),n({hour:a,minute:u})}})]})},G=n(80),R=n(122),H=n(79),U=function(e){var t=e.animating,n=Object(G.a)(e,["animating"]);return t?Object(J.jsx)(I.a,Object(i.a)(Object(i.a)({},n),{},{disabled:!0,children:Object(J.jsx)(R.a,{color:Object(H.get)(n,"background.dark",!1)?"#FFF":"brand"})})):Object(J.jsx)(I.a,Object(i.a)(Object(i.a)({},n),{},{children:n.children}))},X=function(){var e=Object(h.a)(["token"]),t=Object(j.a)(e,3),n=t[0],a=t[1],c=t[2],s=r.a.useState(null),l=Object(j.a)(s,2),m=l[0],x=l[1],p=r.a.useState(5),O=Object(j.a)(p,2),g=O[0],f=O[1],G=r.a.useState(null),R=Object(j.a)(G,2),H=R[0],X=R[1],q=r.a.useState(null),K=Object(j.a)(q,2),Q=K[0],V=K[1],Y=r.a.useState(null),$=Object(j.a)(Y,2),ee=$[0],te=$[1],ne=r.a.useState(null),ae=Object(j.a)(ne,2),re=ae[0],ce=ae[1],se=r.a.useState(!1),ie=Object(j.a)(se,2),oe=ie[0],le=ie[1],ue=[W.DateTime.local(2021,4,1),W.DateTime.local(2021,5,31)],de=r.a.useCallback(Object(d.a)(u.a.mark((function e(){var t;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(t=null,!Q){e.next=7;break}return e.next=4,w(Q.value,g);case 4:t=e.sent,e.next=10;break;case 7:return e.next=9,v(g);case 9:t=e.sent;case 10:if(null!==t){e.next=14;break}return c("token"),e.abrupt("return");case 14:x(t),a("token",t.token,{secure:!0}),t.impersonateList&&X(t.impersonateList.map((function(e){return{label:e[0],value:e[1]}}))),le(!1);case 18:case"end":return e.stop()}}),e)}))),[g,Q,c,a]),je=r.a.useMemo((function(){return!!n.token&&(null===m||(m.month!==g||(!!Q!==!!m.impersonating||!(!Q||!m.impersonating||m.phoneNumber===Q.value))))}),[g,n.token,Q,m]);r.a.useEffect((function(){console.log("rerendering"),je&&de()}),[de,je]);var he=r.a.useCallback((function(e){var t=e.date,n=null,a=W.DateTime.fromJSDate(t),r=a.day;if(null!==m&&m.eventData.length>=r){var c=m.eventData[r-1];a.month===g&&("taken"===c.day_status?n="status-ok":"missed"===c.day_status?n="status-error":"skip"===c.day_status&&(n="status-warning"))}return Object(J.jsx)(C.a,{align:"center",justify:"center",margin:{vertical:"xsmall"},children:Object(J.jsx)(C.a,{width:"30px",height:"30px",round:"medium",background:{color:n},align:"center",justify:"center",children:Object(J.jsx)(S.a,{children:r})})})}),[g,m]),be=r.a.useCallback((function(e){return console.log(e),e.label}),[]),me=function(e){return e.hour<4?e.plus({days:1}):e},xe=r.a.useMemo((function(){if(console.log("recomputing"),null===re)return!0;if(null===m)return!0;var e=me(W.DateTime.utc(2021,5,1,re.start_hour,re.start_minute).setZone("local").set({month:5,day:1})),t=me(W.DateTime.utc(2021,5,1,re.end_hour,re.end_minute).setZone("local").set({month:5,day:1}));if(t<e.plus({minutes:30}))return!1;var n,a=Object(o.a)(m.doseWindows);try{for(a.s();!(n=a.n()).done;){var r=n.value;if(r.id!==re.id){var c=me(W.DateTime.utc(2021,5,1,r.start_hour,r.start_minute).setZone("local").set({month:5,day:1})),s=me(W.DateTime.utc(2021,5,1,r.end_hour,r.end_minute).setZone("local").set({month:5,day:1}));if(e<=c&&c<=t)return!1;if(e<=s&&s<=t)return!1}}}catch(i){a.e(i)}finally{a.f()}return!0}),[re,m]),pe=r.a.useMemo((function(){var e=W.DateTime.local();return e.hour>4&&e.hour<12?"morning":e.hour>12&&e.hour<18?"afternoon":"evening"}),[]),Oe=r.a.useMemo((function(){var e=W.DateTime.local();return g===e.month?e:e.set({month:g,day:1})}),[g]),ge=r.a.useMemo((function(){return(e=["\ud83d\udcab","\ud83c\udf08","\ud83c\udf31","\ud83c\udfc6","\ud83d\udcc8","\ud83d\udc8e","\ud83d\udca1","\ud83d\udd06","\ud83d\udd14"])[Math.floor(e.length*Math.random())];var e}),[]),fe=r.a.useCallback((function(){var e=W.DateTime.utc(2021,5,1,re.start_hour,re.start_minute),t=W.DateTime.utc(2021,5,1,re.end_hour,re.end_minute);return Object(J.jsxs)(J.Fragment,{children:[Object(J.jsx)(B,{value:e.setZone("local"),color:"dark-3",onChangeTime:function(e){var t=W.DateTime.local(2021,5,1,e.hour,e.minute).setZone("UTC");ce(Object(i.a)(Object(i.a)({},re),{},{start_hour:t.hour,start_minute:t.minute}))}}),Object(J.jsx)(B,{value:t.setZone("local"),color:"dark-3",onChangeTime:function(e){console.log("changed time to ".concat(JSON.stringify(e)));var t=W.DateTime.local(2021,5,1,e.hour,e.minute).setZone("UTC");ce(Object(i.a)(Object(i.a)({},re),{},{end_hour:t.hour,end_minute:t.minute}))}}),Object(J.jsx)(U,{onClick:function(){le(!0),k(re),de(),ce(null)},label:xe?"Update":"Invalid dose window",disabled:!xe,animating:oe})]})}),[oe,re,de,xe]);if(!n.token)return Object(J.jsx)(b.a,{to:"/login"});return Object(J.jsxs)(C.a,{children:[null!==H?Object(J.jsxs)(C.a,{direction:"row",align:"center",gap:"small",pad:{horizontal:"medium"},children:[Object(J.jsx)(S.a,{children:"Impersonating:"}),Object(J.jsx)(T.a,{options:H,children:be,onChange:function(e){var t=e.option;console.log("setting"),V(t)}})]}):null,Object(J.jsx)(C.a,{align:"center",children:Object(J.jsxs)(D.a,{size:"small",children:["Good ",pe,m?", ".concat(m.patientName):"","."]})}),Object(J.jsx)(C.a,{children:m&&m.doseToTakeNow?Object(J.jsx)(C.a,{align:"center",background:{color:"status-warning",dark:!0},round:"medium",margin:{horizontal:"large"},pad:{vertical:"medium"},animation:{type:"pulse",size:"medium",duration:2e3},children:Object(J.jsx)(S.a,{alignSelf:"center",margin:{vertical:"none"},children:"Dose to take now!"})}):Object(J.jsx)(C.a,{align:"center",background:{color:"brand",dark:!0},round:"medium",margin:{horizontal:"large"},children:Object(J.jsxs)(S.a,{children:["No doses to take right now. ",ge]})})}),Object(J.jsx)(C.a,{margin:{vertical:"medium"},pad:{horizontal:"large"},children:Object(J.jsx)(_.a,{icon:Object(J.jsx)(E.a,{}),label:"How do I use Coherence?",dropContent:Object(J.jsxs)(C.a,{pad:{horizontal:"small"},children:[Object(J.jsx)(S.a,{textAlign:"center",children:"Texting commands"}),Object(J.jsxs)(A.a,{columns:["xsmall","small"],children:[Object(J.jsx)(S.a,{size:"small",children:"T, taken"}),Object(J.jsx)(S.a,{size:"small",children:"Mark your medication as taken at the current time"}),Object(J.jsx)(S.a,{size:"small",children:"T @ 5:00pm"}),Object(J.jsx)(S.a,{size:"small",children:"Mark your medication as taken at 5pm"}),Object(J.jsx)(S.a,{size:"small",children:"S, skip"}),Object(J.jsx)(S.a,{size:"small",children:"Skip the current dose"}),Object(J.jsx)(S.a,{size:"small",children:"1"}),Object(J.jsx)(S.a,{size:"small",children:"Delay the reminder by ten minutes"}),Object(J.jsx)(S.a,{size:"small",children:"2"}),Object(J.jsx)(S.a,{size:"small",children:"Delay the reminder by half an hour"}),Object(J.jsx)(S.a,{size:"small",children:"3"}),Object(J.jsx)(S.a,{size:"small",children:"Delay the reminder by an hour"}),Object(J.jsx)(S.a,{size:"small",children:"20, 20 min"}),Object(J.jsx)(S.a,{size:"small",children:"Delay the reminder by 20 minutes"}),Object(J.jsx)(S.a,{size:"small",children:"W, website, site"}),Object(J.jsx)(S.a,{size:"small",children:"Get the website linke sent to you"}),Object(J.jsx)(S.a,{size:"small",children:"Eating, going for a walk"}),Object(J.jsx)(S.a,{size:"small",children:"Tell Coherence you're busy with an activity"}),Object(J.jsx)(S.a,{size:"small",children:"X"}),Object(J.jsx)(S.a,{size:"small",children:"Report an error"})]})]}),dropAlign:{top:"bottom"}})}),Object(J.jsxs)(C.a,{pad:"medium",background:{color:"light-3"},children:[Object(J.jsx)(S.a,{textAlign:"center",margin:{vertical:"none"},fill:!0,children:"Medication history"}),Object(J.jsx)(M.a,{date:Oe.toISO(),fill:!0,onSelect:function(e){var t=W.DateTime.fromISO(e);te(t.day)},showAdjacentDays:!1,bounds:ue.map((function(e){return e.toString()})),children:he,daysOfWeek:!0,onReference:function(e){f(W.DateTime.fromISO(e).month),x(Object(i.a)(Object(i.a)({},m),{},{eventData:[]}))},animate:!1})]}),ee&&Object(J.jsx)(F.a,{onEsc:function(){return te(!1)},onClickOutside:function(){return te(!1)},responsive:!1,children:Object(J.jsxs)(C.a,{width:"70vw",pad:"large",children:[Object(J.jsxs)(C.a,{direction:"row",justify:"between",children:[Object(J.jsxs)(S.a,{size:"large",children:[W.DateTime.local().set({month:g}).monthLong," ",ee]}),Object(J.jsx)(I.a,{icon:Object(J.jsx)(N.a,{}),onClick:function(){return te(!1)}})]}),m.eventData[ee-1].day_status?Object.keys(m.eventData[ee-1].time_of_day).sort((function(e,t){return e===t?0:"morning"===e||"afternoon"===e&&"evening"===t?-1:1})).map((function(e){var t=m.eventData[ee-1].time_of_day[e][0];return Object(J.jsxs)(J.Fragment,{children:[Object(J.jsxs)(S.a,{margin:{bottom:"none"},children:[e," dose"]},"tod-".concat(e)),Object(J.jsxs)(C.a,{pad:{left:"medium"},direction:"row",align:"center",justify:"between",children:[Object(J.jsxs)(S.a,{size:"small",children:[t.type,t.time?" at ".concat(W.DateTime.fromJSDate(new Date(t.time)).toLocaleString(W.DateTime.TIME_SIMPLE)):""]},"todStatus-".concat(e)),"taken"===t.type?Object(J.jsx)(P.a,{color:"status-ok",size:"small"}):null,"skipped"===t.type?Object(J.jsx)(L.a,{color:"status-warning",size:"small"}):null,"missed"===t.type?Object(J.jsx)(N.a,{color:"status-error",size:"small"}):null]},"todStatusContainer-".concat(e))]})})):Object(J.jsx)(S.a,{children:"No data for this day."})]})}),Object(J.jsxs)(C.a,{align:"center",pad:{vertical:"medium"},margin:{horizontal:"xlarge"},border:"bottom",children:[Object(J.jsx)(S.a,{textAlign:"center",margin:{vertical:"none"},children:"Dose windows"}),m?m.doseWindows.map((function(e){var t=W.DateTime.utc(2021,5,1,e.start_hour,e.start_minute),n=W.DateTime.utc(2021,5,1,e.end_hour,e.end_minute);return Object(J.jsxs)(A.a,{columns:["small","xsmall"],align:"center",pad:{horizontal:"large"},alignContent:"center",justifyContent:"center",justify:"center",children:[Object(J.jsxs)(C.a,{direction:"row",align:"center",children:[Object(J.jsx)(S.a,{children:t.setZone("local").toLocaleString(W.DateTime.TIME_SIMPLE)}),Object(J.jsx)(Z.a,{}),Object(J.jsx)(S.a,{children:n.setZone("local").toLocaleString(W.DateTime.TIME_SIMPLE)})]}),Object(J.jsx)(I.a,{label:"edit",onClick:function(){return ce(e)}})]},"doseWindowContainer-".concat(e.id))})):null]}),re&&Object(J.jsx)(F.a,{onEsc:function(){return ce(null)},onClickOutside:function(){return ce(null)},responsive:!1,children:Object(J.jsxs)(C.a,{width:"90vw",pad:"large",children:[Object(J.jsxs)(C.a,{direction:"row",justify:"between",children:[Object(J.jsx)(S.a,{size:"large",children:"Edit dose window"}),Object(J.jsx)(I.a,{icon:Object(J.jsx)(N.a,{}),onClick:function(){return ce(null)}})]}),Object(J.jsx)(C.a,{children:fe(re)})]})}),Object(J.jsx)(C.a,{align:"center",pad:{vertical:"medium"},children:m?Object(J.jsxs)(J.Fragment,{children:[Object(J.jsx)(S.a,{textAlign:"center",margin:{vertical:"none"},children:"Pause / resume Coherence"}),Object(J.jsxs)(S.a,{size:"small",color:"dark-3",children:["Coherence is currently ",m.pausedService?"paused":"active","."]}),Object(J.jsxs)(U,{background:m.pausedService?{dark:!0}:null,animating:oe,style:{padding:"10px"},primary:m.pausedService,onClick:Object(d.a)(u.a.mark((function e(){return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(le(!0),!m.pausedService){e.next=6;break}return e.next=4,z();case 4:e.next=8;break;case 6:return e.next=8,y();case 8:de();case 9:case"end":return e.stop()}}),e)}))),children:[m.pausedService?"Resume":"Pause"," Coherence"]}),m.pausedService?Object(J.jsx)(S.a,{size:"small",color:"status-warning",textAlign:"center",children:"While Coherence is paused, we can't respond to any texts you send us, or remind you about your medications."}):null]}):null}),Object(J.jsxs)(C.a,{align:"center",pad:{vertical:"medium"},margin:{horizontal:"xlarge"},border:"top",children:[Object(J.jsx)(S.a,{textAlign:"center",margin:{vertical:"none"},children:"Need help with anything?"}),Object(J.jsx)(S.a,{size:"small",color:"dark-3",children:"Our customer service is just a text away at (650) 667-1146. Reach out any time and we'll get back to you in a few hours!"})]}),Object(J.jsx)(C.a,{align:"center",pad:{vertical:"medium"},margin:{horizontal:"xlarge"},border:"top",children:Object(J.jsx)(I.a,{onClick:function(){c("token")},children:"Log out"})})]})},q=n(139),K=n(130),Q=n(131),V=n(132),Y=n(133),$=function(){var e=r.a.useState(""),t=Object(j.a)(e,2),n=t[0],a=t[1],c=r.a.useState(""),s=Object(j.a)(c,2),i=s[0],o=s[1],l=r.a.useState(""),m=Object(j.a)(l,2),x=m[0],p=m[1],O=r.a.useState(""),g=Object(j.a)(O,2),v=g[0],w=g[1],k=r.a.useState("phoneNumber"),y=Object(j.a)(k,2),z=y[0],T=y[1],_=Object(h.a)(["token"]),A=Object(j.a)(_,2),M=A[0],F=A[1],E=r.a.useState(!1),N=Object(j.a)(E,2),P=N[0],L=N[1],Z=r.a.useCallback(Object(d.a)(u.a.mark((function e(){var t;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,f(n,i,x);case 2:null===(t=e.sent)?L(!0):("success"===t.status&&(console.log("setting cookie"),F("token",t.token,{secure:!0})),T(t.status),L(!1));case 4:case"end":return e.stop()}}),e)}))),[x,n,i,F]),W=r.a.useCallback((function(){return"phoneNumber"===z?Object(J.jsxs)(J.Fragment,{children:[Object(J.jsx)(S.a,{textAlign:"center",size:"small",children:"Enter phone number."}),Object(J.jsx)(q.a,{icon:Object(J.jsx)(K.a,{}),placeholder:"(555) 555-5555",size:"small",value:n,onChange:function(e){a(e.target.value)}}),P?Object(J.jsx)(S.a,{size:"small",children:"Invalid phone number."}):null]}):"2fa"===z?Object(J.jsxs)(J.Fragment,{children:[Object(J.jsx)(S.a,{textAlign:"center",size:"small",children:"We've texted you a secret code, enter it below."}),Object(J.jsx)(q.a,{icon:Object(J.jsx)(Q.a,{}),placeholder:"123456",size:"small",value:i,onChange:function(e){o(e.target.value)}}),P?Object(J.jsx)(S.a,{size:"small",children:"Invalid secret code."}):null]}):"password"===z?Object(J.jsxs)(J.Fragment,{children:[Object(J.jsx)(S.a,{textAlign:"center",size:"small",children:"Enter password."}),Object(J.jsx)(q.a,{icon:Object(J.jsx)(V.a,{}),placeholder:"\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022",size:"small",value:x,onChange:function(e){p(e.target.value),w(e.target.value)},type:"password"}),P?Object(J.jsx)(S.a,{size:"small",children:"Invalid password. If you'd like us to reset it, give us a text at (650) 667-1146."}):null]}):"register"===z?Object(J.jsxs)(J.Fragment,{children:[Object(J.jsx)(S.a,{textAlign:"center",size:"small",children:"Create your password."}),Object(J.jsx)(q.a,{icon:Object(J.jsx)(V.a,{}),placeholder:"Enter password",size:"small",value:x,onChange:function(e){p(e.target.value)},type:"password"}),Object(J.jsx)(q.a,{icon:Object(J.jsx)(V.a,{}),placeholder:"Type it again",size:"small",value:v,onChange:function(e){w(e.target.value)},type:"password"}),x!==v?Object(J.jsx)(S.a,{size:"small",children:"Passwords don't match."}):null]}):void 0}),[P,z,x,v,n,i]);return M.token?Object(J.jsx)(b.a,{to:"/"}):Object(J.jsxs)(C.a,{height:"100vh",flex:"grow",background:{position:"center",dark:!1,opacity:"strong"},children:[Object(J.jsxs)(C.a,{height:"40vh",align:"center",justify:"center",pad:"large",children:[Object(J.jsx)(S.a,{children:"welcome to"}),Object(J.jsx)(D.a,{children:"coherence"})]}),Object(J.jsxs)(C.a,{height:"60vh",align:"center",justify:"between",background:{color:"brand",dark:!0},pad:"large",children:[Object(J.jsx)(S.a,{color:"white",textAlign:"center",children:"Peace of mind with your medications is just around the corner."}),Object(J.jsxs)(C.a,{children:[Object(J.jsx)(C.a,{width:"200px",margin:{bottom:"medium",top:"xsmall"},children:W()}),Object(J.jsx)(I.a,{label:"submit",icon:Object(J.jsx)(Y.a,{}),onClick:Z,disabled:x!==v})]})]})]})},ee=n(38),te=function(){return Object(J.jsx)(ee.a,{children:Object(J.jsxs)(b.d,{children:[Object(J.jsx)(b.b,{exact:!0,path:"/",render:function(){return Object(J.jsx)(X,{})}}),Object(J.jsx)(b.b,{exact:!0,path:"/login",render:function(){return Object(J.jsx)($,{})}})]})})},ne=function(e){e&&e instanceof Function&&n.e(3).then(n.bind(null,143)).then((function(t){var n=t.getCLS,a=t.getFID,r=t.getFCP,c=t.getLCP,s=t.getTTFB;n(e),a(e),r(e),c(e),s(e)}))},ae=n(134),re=n(138);s.a.render(Object(J.jsx)(r.a.StrictMode,{children:Object(J.jsx)(ae.a,{children:Object(J.jsx)(re.a,{theme:{global:{colors:{brand:"#002864",text:{light:"#002864"},paragraph:{light:"#002864"},background:"#FFF"}},spinner:{container:{color:{light:"#002864",dark:"FFF"}}}},themeMode:"light",children:Object(J.jsx)(te,{})})})}),document.getElementById("root")),ne()},90:function(e,t,n){},91:function(e,t,n){}},[[104,1,2]]]);
//# sourceMappingURL=main.c998dfc3.chunk.js.map