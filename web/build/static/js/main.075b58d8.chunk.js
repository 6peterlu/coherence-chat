(this.webpackJsonpweb=this.webpackJsonpweb||[]).push([[0],{149:function(e,t,n){},150:function(e,t,n){},268:function(e,t,n){"use strict";n.r(t);var a=n(0),r=n.n(a),c=n(38),i=n.n(c),l=(n(149),n(150),n(16)),o=n(10),s=n(6),u=n.n(s),d=n(14),j=n(11),b=n(288),h=n(12),m=n(121),g=new(n(41).a);console.log("production");var p="production"==="production".trim()?"https://coherence-chat.herokuapp.com":"http://localhost:5000",x=function(){var e=Object(d.a)(u.a.mark((function e(t,n){var a,r,c,i;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return a=g.get("token"),r={Accept:"application/json","Content-Type":"application/json","Access-Control-Allow_Methods":"POST","Access-Control_Allow_Headers":"*","Access-Control-Allow-Origin":"*"},a&&(r.Authorization="Basic "+btoa(a+":unused")),e.next=5,fetch("".concat(p,"/").concat(t),{method:"post",headers:r,body:JSON.stringify(n)});case 5:if(!(c=e.sent).ok){e.next=11;break}return e.next=9,c.text();case 9:return i=e.sent,e.abrupt("return",JSON.parse(i));case 11:return console.log("POST call to /".concat(t," errored with status ").concat(c.status)),e.abrupt("return",null);case 13:case"end":return e.stop()}}),e)})));return function(t,n){return e.apply(this,arguments)}}(),O=function(){var e=Object(d.a)(u.a.mark((function e(t,n){var a,r,c,i,l;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return a="".concat(p,"/").concat(t),a+="?".concat(m.stringify(n)),r=g.get("token"),c={Accept:"application/json","Access-Control-Allow-Methods":"GET","Access-Control-Allow-Headers":"*","Access-Control-Allow-Origin":"*"},r&&(c.Authorization="Basic "+btoa(r+":unused")),e.next=7,fetch(a,{method:"get",headers:c});case 7:if(!(i=e.sent).ok){e.next=13;break}return e.next=11,i.text();case 11:return l=e.sent,e.abrupt("return",JSON.parse(l));case 13:return console.log("GET call to /".concat(t," errored with status ").concat(i.status)),e.abrupt("return",null);case 15:case"end":return e.stop()}}),e)})));return function(t,n){return e.apply(this,arguments)}}(),f=function(){var e=Object(d.a)(u.a.mark((function e(t,n,a){var r;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,x("login/new",{phoneNumber:t,secretCode:n,password:a});case 2:return r=e.sent,e.abrupt("return",r);case 4:case"end":return e.stop()}}),e)})));return function(t,n,a){return e.apply(this,arguments)}}(),v=function(){var e=Object(d.a)(u.a.mark((function e(t){var n;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,O("patientData/new",{calendarMonth:t});case 2:return n=e.sent,e.abrupt("return",n);case 4:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}(),w=function(){var e=Object(d.a)(u.a.mark((function e(t,n){var a;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,O("patientData/new",{phoneNumber:t,calendarMonth:n});case 2:return a=e.sent,e.abrupt("return",a);case 4:case"end":return e.stop()}}),e)})));return function(t,n){return e.apply(this,arguments)}}(),y=function(){var e=Object(d.a)(u.a.mark((function e(t){var n;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,x("doseWindow/update/new",{updatedDoseWindow:t});case 2:return n=e.sent,e.abrupt("return",n);case 4:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}(),k=function(){var e=Object(d.a)(u.a.mark((function e(t){var n;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,x("doseWindow/deactivate/new",{doseWindowId:t});case 2:return n=e.sent,e.abrupt("return",n);case 4:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}(),z=function(){var e=Object(d.a)(u.a.mark((function e(){var t;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,x("user/pause/new");case 2:return t=e.sent,e.abrupt("return",t);case 4:case"end":return e.stop()}}),e)})));return function(){return e.apply(this,arguments)}}(),C=function(){var e=Object(d.a)(u.a.mark((function e(){var t;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,x("user/resume/new");case 2:return t=e.sent,e.abrupt("return",t);case 4:case"end":return e.stop()}}),e)})));return function(){return e.apply(this,arguments)}}(),S=function(){var e=Object(d.a)(u.a.mark((function e(t){var n;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,x("user/healthMetrics/set",{metricList:t});case 2:return n=e.sent,e.abrupt("return",n);case 4:case"end":return e.stop()}}),e)})));return function(t){return e.apply(this,arguments)}}(),T=n(22);T.a.initialize("UA-196778289-2",{cookieFlags:"max-age=7200;SameSite=None;Secure"});var D="production"==="production".trim(),_=function(e){D&&T.a.event({category:"Churn",action:"Paused service",label:e})},A=n(71),F=n(96),I=n(307),E=n(301),M=n(308),L=n(286),N=n(309),P=n(303),W=n(304),Z=n(270),R=n(302),H=n(289),J=n(291),G=n(292),B=n(293),U=n(294),Y=n(295),V=n(5),X=(n(260),n(2)),q=function(e){var t=e.value,n=e.onChangeTime,a=r.a.useState(t.hour),c=Object(j.a)(a,2),i=c[0],l=c[1],o=r.a.useState(t.minute),s=Object(j.a)(o,2),u=s[0],d=s[1];return Object(X.jsxs)(F.a,{direction:"row",children:[Object(X.jsx)(E.a,{options:[1,2,3,4,5,6,7,8,9,10,11,12],value:i>12?i-12:0===i?12:i,plain:!0,onChange:function(e){var t=e.value,a=i>=12?t+12:t%12;l(a),n({hour:a,minute:u})}}),Object(X.jsx)(E.a,{options:["00","15","30","45"],value:"".concat(0===u?"0":"").concat(u.toString()),plain:!0,onChange:function(e){var t=e.value;d(parseInt(t)),n({hour:i,minute:parseInt(t)})}}),Object(X.jsx)(E.a,{options:["AM","PM"],value:i>=12?"PM":"AM",plain:!0,onChange:function(e){var t=e.value,a=i;"AM"===t?i>=12&&(a=i-12,l(i-12)):i<12&&(a=i+12,l(i+12)),n({hour:a,minute:u})}})]})},K=n(139),Q=n(287),$=n(138),ee=function(e){var t=e.animating,n=Object(K.a)(e,["animating"]);return t?Object(X.jsx)(Z.a,Object(l.a)(Object(l.a)({},n),{},{alignSelf:"center",label:null,disabled:!0,children:Object(X.jsx)(Q.a,{color:Object($.get)(n,"background.dark",!1)?"#FFF":"brand"})})):Object(X.jsx)(Z.a,Object(l.a)(Object(l.a)({},n),{},{children:n.children}))},te=function(){console.log(V.DateTime.local().zoneName);var e=Object(b.a)(["token"]),t=Object(j.a)(e,3),n=t[0],a=t[1],c=t[2],i=r.a.useState(null),s=Object(j.a)(i,2),m=s[0],g=s[1],p=r.a.useState(5),x=Object(j.a)(p,2),O=x[0],f=x[1],K=r.a.useState(null),Q=Object(j.a)(K,2),$=Q[0],te=Q[1],ne=r.a.useState(null),ae=Object(j.a)(ne,2),re=ae[0],ce=ae[1],ie=r.a.useState(null),le=Object(j.a)(ie,2),oe=le[0],se=le[1],ue=r.a.useState(null),de=Object(j.a)(ue,2),je=de[0],be=de[1],he=r.a.useState(null),me=Object(j.a)(he,2),ge=me[0],pe=me[1],xe=r.a.useState(null),Oe=Object(j.a)(xe,2),fe=Oe[0],ve=Oe[1],we=r.a.useState({label:"all time",value:null}),ye=Object(j.a)(we,2),ke=ye[0],ze=ye[1];console.log(ke);var Ce=r.a.useState(!1),Se=Object(j.a)(Ce,2),Te=Se[0],De=Se[1],_e=[V.DateTime.local(2021,4,1),V.DateTime.local(2021,5,31)],Ae=r.a.useCallback(Object(d.a)(u.a.mark((function e(){var t;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(t=null,!re){e.next=7;break}return e.next=4,w(re.value,O);case 4:t=e.sent,e.next=10;break;case 7:return e.next=9,v(O);case 9:t=e.sent;case 10:if(null!==t){e.next=14;break}return c("token"),e.abrupt("return");case 14:console.log(t),g(t),null===t.impersonateList&&(n=t.patientId,D&&T.a.event({category:"Engagement",action:"Loaded homepage",label:n})),a("token",t.token,{secure:!0}),t.impersonateList&&te(t.impersonateList.map((function(e){return{label:e[0],value:e[1]}}))),De(!1);case 20:case"end":return e.stop()}var n}),e)}))),[O,re,c,a]),Fe=r.a.useMemo((function(){return!!n.token&&(null===m||(m.month!==O||(!!re!==!!m.impersonating||!(!re||!m.impersonating||m.phoneNumber===re.value))))}),[O,n.token,re,m]);r.a.useEffect((function(){console.log("rerendering"),Fe&&Ae()}),[Ae,Fe]);var Ie=r.a.useCallback((function(e){var t=e.date,n=null,a=V.DateTime.fromJSDate(t),r=a.day;if(null!==m&&m.eventData.length>=r){var c=m.eventData[r-1];a.month===O&&("taken"===c.day_status?n="status-ok":"missed"===c.day_status?n="status-error":"skip"===c.day_status&&(n="status-warning"))}return Object(X.jsx)(F.a,{align:"center",justify:"center",margin:{vertical:"xsmall"},children:Object(X.jsx)(F.a,{width:"30px",height:"30px",round:"medium",background:{color:n},align:"center",justify:"center",children:Object(X.jsx)(I.a,{children:r})})})}),[O,m]),Ee=r.a.useMemo((function(){var e={weight:"pounds",glucose:"mg/dL","blood pressure":"mm/hg"},t={};if(null!==m)for(var n in m.healthMetricData){var a=m.healthMetricData[n];console.log(a),t[n]="blood pressure"!==n?{datasets:[{data:a.map((function(e){return{x:V.DateTime.fromHTTP(e.time),y:e.value}})),label:n,fill:!1,backgroundColor:"rgb(255, 99, 132)",borderColor:"rgba(255, 99, 132, 0.2)"}],options:{scales:{x:{type:"time",time:{unit:"day"},grid:{color:["#777"]},ticks:{color:"#FFF"},min:null!==ke.value?V.DateTime.local().minus({days:ke.value}).toISODate():null},y:{grid:{color:["#AAA"]},ticks:{color:"#FFF"},title:{text:e[n],display:!0,color:"#FFF"}}},color:"white",plugins:{legend:{display:!1}},elements:{point:{hitRadius:10,hoverRadius:10}},showLine:!0}}:{datasets:[{data:a.map((function(e){return{x:V.DateTime.fromHTTP(e.time),y:e.value.systolic}})),label:"systolic",fill:!1,backgroundColor:"rgb(255, 99, 132)",borderColor:"rgba(255, 99, 132, 0.2)"},{data:a.map((function(e){return{x:V.DateTime.fromHTTP(e.time),y:e.value.diastolic}})),label:"diastolic",fill:!1,backgroundColor:"rgb(99, 255, 132)",borderColor:"rgba(99, 255, 132, 0.2)"}],options:{scales:{x:{type:"time",time:{unit:"day"},grid:{color:["#777"]},ticks:{color:"#FFF"},min:null!==ke.value?V.DateTime.local().minus({days:ke.value}).toISODate():null},y:{grid:{color:["#AAA"]},ticks:{color:"#FFF"},title:{text:e[n],display:!0,color:"#FFF"}}},color:"white",plugins:{datalabels:{color:"black"}},showLine:!0}}}return console.log("returned HM data:"),console.log(t),t}),[m,ke]),Me=r.a.useCallback((function(e){return console.log(e),e.label}),[]),Le=function(e){return e.hour<4?e.plus({days:1}):e},Ne=r.a.useMemo((function(){if(console.log("recomputing"),null===je)return!0;if(null===m)return!0;var e=Le(V.DateTime.utc(2021,5,1,je.start_hour,je.start_minute).setZone("local").set({month:5,day:1})),t=Le(V.DateTime.utc(2021,5,1,je.end_hour,je.end_minute).setZone("local").set({month:5,day:1}));if(t<e.plus({minutes:30}))return!1;var n,a=Object(o.a)(m.doseWindows);try{for(a.s();!(n=a.n()).done;){var r=n.value;if(r.id!==je.id){var c=Le(V.DateTime.utc(2021,5,1,r.start_hour,r.start_minute).setZone("local").set({month:5,day:1})),i=Le(V.DateTime.utc(2021,5,1,r.end_hour,r.end_minute).setZone("local").set({month:5,day:1}));if(e<=c&&c<=t)return!1;if(e<=i&&i<=t)return!1}}}catch(l){a.e(l)}finally{a.f()}return!0}),[je,m]),Pe=r.a.useMemo((function(){var e=V.DateTime.local();return e.hour>4&&e.hour<12?"morning":e.hour>12&&e.hour<18?"afternoon":"evening"}),[]),We=r.a.useMemo((function(){var e=V.DateTime.local();return O===e.month?e:e.set({month:O,day:1})}),[O]),Ze=r.a.useMemo((function(){return(e=["\ud83d\udcab","\ud83c\udf08","\ud83c\udf31","\ud83c\udfc6","\ud83d\udcc8","\ud83d\udc8e","\ud83d\udca1","\ud83d\udd06","\ud83d\udd14"])[Math.floor(e.length*Math.random())];var e}),[]),Re=r.a.useCallback((function(){if(null===m)return null;var e=V.DateTime.utc(2021,5,1,je.start_hour,je.start_minute),t=V.DateTime.utc(2021,5,1,je.end_hour,je.end_minute);return Object(X.jsxs)(X.Fragment,{children:[Object(X.jsx)(I.a,{size:"small",margin:{bottom:"none"},children:"Start time (earliest time you'll be reminded)"}),Object(X.jsx)(q,{value:e.setZone("local"),color:"dark-3",onChangeTime:function(e){var t=V.DateTime.local(2021,5,1,e.hour,e.minute).setZone("UTC");be(Object(l.a)(Object(l.a)({},je),{},{start_hour:t.hour,start_minute:t.minute}))}}),Object(X.jsx)(I.a,{size:"small",margin:{bottom:"none"},children:"End time (latest time you'll be reminded)"}),Object(X.jsx)(q,{value:t.setZone("local"),color:"dark-3",onChangeTime:function(e){console.log("changed time to ".concat(JSON.stringify(e)));var t=V.DateTime.local(2021,5,1,e.hour,e.minute).setZone("UTC");be(Object(l.a)(Object(l.a)({},je),{},{end_hour:t.hour,end_minute:t.minute}))}}),Object(X.jsx)(ee,{onClick:Object(d.a)(u.a.mark((function e(){return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return De(!0),console.log("set animating"),e.next=4,y(je);case 4:return e.next=6,Ae();case 6:be(null),null===$&&(t=m.patientId,D&&T.a.event({category:"Engagement",action:"Submit edited dose window",label:t}));case 8:case"end":return e.stop()}var t}),e)}))),label:Ne?je.id?"Update":"Create":"Invalid dose window",disabled:!Ne,animating:Te}),je.id?Object(X.jsx)(ee,{onClick:function(){var e;pe(je),null===$&&(e=m.patientId,D&&T.a.event({category:"Engagement",action:"Start deleting dose window",label:e}))},disabled:Te,size:"small",padding:{horizontal:"none"},margin:{top:"medium"},label:"Delete dose window",color:"status-error",plain:!0,alignSelf:"center"}):null]})}),[Te,je,$,Ae,m,Ne]);if(!n.token)return Object(X.jsx)(h.a,{to:"/login"});return console.log(ke.label),Object(X.jsxs)(F.a,{children:[null!==$?Object(X.jsxs)(F.a,{direction:"row",align:"center",gap:"small",pad:{horizontal:"medium"},children:[Object(X.jsx)(I.a,{children:"Impersonating:"}),Object(X.jsx)(E.a,{options:$,children:Me,onChange:function(e){var t=e.option;console.log("setting"),ce(t)}})]}):null,Object(X.jsx)(F.a,{align:"center",children:Object(X.jsxs)(M.a,{size:"small",children:["Good ",Pe,m?", ".concat(m.patientName):"","."]})}),Object(X.jsx)(F.a,{children:m&&m.takeNow?Object(X.jsx)(F.a,{align:"center",background:{color:"status-warning",dark:!0},round:"medium",margin:{horizontal:"large"},pad:{vertical:"medium"},animation:{type:"pulse",size:"medium",duration:2e3},children:Object(X.jsx)(I.a,{alignSelf:"center",margin:{vertical:"none"},children:"Dose to take now!"})}):Object(X.jsx)(F.a,{align:"center",background:{color:"brand",dark:!0},round:"medium",margin:{horizontal:"large"},children:Object(X.jsxs)(I.a,{children:["No doses to take right now. ",Ze]})})}),Object(X.jsx)(F.a,{margin:{vertical:"medium"},pad:{horizontal:"large"},children:Object(X.jsx)(L.a,{icon:Object(X.jsx)(H.a,{}),label:"How do I use Coherence?",dropContent:Object(X.jsxs)(F.a,{pad:{horizontal:"small"},children:[Object(X.jsx)(I.a,{textAlign:"center",children:"Texting commands"}),Object(X.jsxs)(N.a,{columns:["xsmall","small"],align:"center",justifyContent:"center",gap:{column:"small"},children:[Object(X.jsx)(I.a,{size:"small",children:"T, taken"}),Object(X.jsx)(I.a,{size:"small",children:"Mark your medication as taken at the current time"}),Object(X.jsx)(I.a,{size:"small",children:"T @ 5:00pm"}),Object(X.jsx)(I.a,{size:"small",children:"Mark your medication as taken at 5pm"}),Object(X.jsx)(I.a,{size:"small",children:"S, skip"}),Object(X.jsx)(I.a,{size:"small",children:"Skip the current dose"}),Object(X.jsx)(I.a,{size:"small",children:"1"}),Object(X.jsx)(I.a,{size:"small",children:"Delay the reminder by ten minutes"}),Object(X.jsx)(I.a,{size:"small",children:"2"}),Object(X.jsx)(I.a,{size:"small",children:"Delay the reminder by half an hour"}),Object(X.jsx)(I.a,{size:"small",children:"3"}),Object(X.jsx)(I.a,{size:"small",children:"Delay the reminder by an hour"}),Object(X.jsx)(I.a,{size:"small",children:"20, 20 min"}),Object(X.jsx)(I.a,{size:"small",children:"Delay the reminder by 20 minutes"}),Object(X.jsx)(I.a,{size:"small",children:"glucose:140, 140 mg/dL"}),Object(X.jsx)(I.a,{size:"small",children:"Record glucose reading"}),Object(X.jsx)(I.a,{size:"small",children:"weight:150, 150 pounds, 150 lb"}),Object(X.jsx)(I.a,{size:"small",children:"Record weight reading"}),Object(X.jsx)(I.a,{size:"small",children:"120/80, 120 80"}),Object(X.jsx)(I.a,{size:"small",children:"Record blood pressure reading"}),Object(X.jsx)(I.a,{size:"small",children:"W, website, site"}),Object(X.jsx)(I.a,{size:"small",children:"Get the website link sent to you"}),Object(X.jsx)(I.a,{size:"small",children:"Eating, going for a walk"}),Object(X.jsx)(I.a,{size:"small",children:"Tell Coherence you're busy with an activity"}),Object(X.jsx)(I.a,{size:"small",children:"X"}),Object(X.jsx)(I.a,{size:"small",children:"Report an error"})]})]}),dropAlign:{top:"bottom"}})}),Object(X.jsxs)(F.a,{pad:"medium",background:{color:"light-3"},children:[Object(X.jsx)(I.a,{textAlign:"center",margin:{vertical:"none"},fill:!0,children:"Medication history"}),Object(X.jsx)(P.a,{date:We.toISO(),fill:!0,onSelect:function(e){var t,n=V.DateTime.fromISO(e);se(n.day),null===$&&(t=m.patientId,D&&T.a.event({category:"Engagement",action:"Viewed day details",label:t}))},showAdjacentDays:!1,bounds:_e.map((function(e){return e.toString()})),children:Ie,daysOfWeek:!0,onReference:function(e){f(V.DateTime.fromISO(e).month),g(Object(l.a)(Object(l.a)({},m),{},{eventData:[]}))},animate:!1})]}),oe&&Object(X.jsx)(W.a,{onEsc:function(){return se(!1)},onClickOutside:function(){return se(!1)},responsive:!1,children:Object(X.jsxs)(F.a,{width:"70vw",pad:"large",children:[Object(X.jsxs)(F.a,{direction:"row",justify:"between",children:[Object(X.jsxs)(I.a,{size:"large",children:[V.DateTime.local().set({month:O}).monthLong," ",oe]}),Object(X.jsx)(Z.a,{icon:Object(X.jsx)(J.a,{}),onClick:function(){return se(!1)}})]}),m.eventData[oe-1].day_status?Object.keys(m.eventData[oe-1].time_of_day).sort((function(e,t){return e===t?0:"morning"===e||"afternoon"===e&&"evening"===t?-1:1})).map((function(e){var t=m.eventData[oe-1].time_of_day[e].length>1;return m.eventData[oe-1].time_of_day[e].map((function(n,a){return Object(X.jsxs)(X.Fragment,{children:[Object(X.jsxs)(I.a,{margin:{bottom:"none"},children:[e," dose",t?" ".concat(a+1):""]},"tod-".concat(e)),Object(X.jsxs)(F.a,{pad:{left:"medium"},direction:"row",align:"center",justify:"between",children:[Object(X.jsxs)(I.a,{size:"small",children:[n.type,n.time?" at ".concat(V.DateTime.fromJSDate(new Date(n.time)).toLocaleString(V.DateTime.TIME_SIMPLE)):""]},"todStatus-".concat(e)),"taken"===n.type?Object(X.jsx)(G.a,{color:"status-ok",size:"small"}):null,"skipped"===n.type?Object(X.jsx)(B.a,{color:"status-warning",size:"small"}):null,"missed"===n.type?Object(X.jsx)(J.a,{color:"status-error",size:"small"}):null]},"todStatusContainer-".concat(e))]})}))})):Object(X.jsx)(I.a,{children:"No data for this day."})]})}),Object(X.jsxs)(F.a,{align:"center",background:"brand",pad:{bottom:"large"},children:[Object(X.jsx)(I.a,{margin:{bottom:"none"},children:"Health tracking"}),0===Object.keys(Ee).length?Object(X.jsxs)(X.Fragment,{children:[Object(X.jsx)(I.a,{size:"small",children:"You're not tracking any health metrics yet."}),Object(X.jsx)(I.a,{size:"small",textAlign:"center",children:"Tracking is a brand new feature that allows you to text us health data such as blood pressure, weight, or glucose. You can then view your historical data here at any time."})]}):null,0!==Object.keys(Ee).length?Object(X.jsx)(F.a,{margin:{top:"small"},children:Object(X.jsx)(E.a,{options:[{label:"week",value:7},{label:"month",value:30},{label:"3 months",value:90},{label:"year",value:365},{label:"all time",value:null}],children:function(e){return Object(X.jsx)(I.a,{margin:"small",children:e.label})},onChange:function(e){var t=e.value;ze(t)},valueLabel:Object(X.jsx)(I.a,{margin:{vertical:"xsmall",horizontal:"small"},children:ke.label})})}):null,Ee&&"blood pressure"in Ee?Object(X.jsxs)(F.a,{pad:{horizontal:"large"},fill:"horizontal",children:[Object(X.jsx)(I.a,{size:"small",margin:{bottom:"none"},children:"Blood pressure"}),Ee["blood pressure"].datasets[0].data.length>0?Object(X.jsx)(A.a,{data:{datasets:Ee["blood pressure"].datasets},options:Ee["blood pressure"].options}):Object(X.jsx)(I.a,{alignSelf:"center",size:"small",children:'No blood pressure data recorded yet. Example texts you can send: "120/80", "120 80".'})]}):null,Ee&&"weight"in Ee?Object(X.jsxs)(F.a,{pad:{horizontal:"large"},fill:"horizontal",children:[Object(X.jsx)(I.a,{size:"small",margin:{bottom:"none"},children:"Weight"}),Ee.weight.datasets[0].data.length>0?Object(X.jsx)(A.a,{data:{datasets:Ee.weight.datasets},options:Ee.weight.options}):Object(X.jsx)(I.a,{alignSelf:"center",size:"small",children:'No weight data recorded yet. Example texts you can send: "weight:150", "150 lb", "150 pounds".'})]}):null,Ee&&"glucose"in Ee?Object(X.jsxs)(F.a,{pad:{horizontal:"large"},fill:"horizontal",children:[Object(X.jsx)(I.a,{size:"small",margin:{bottom:"none"},children:"Glucose"}),Ee.glucose.datasets[0].data.length>0?Object(X.jsx)(A.a,{data:{datasets:Ee.glucose.datasets},options:Ee.glucose.options}):Object(X.jsx)(I.a,{alignSelf:"center",size:"small",children:'No glucose data recorded yet. Example texts you can send: "glucose:140", "140 mg/dL"'})]}):null,Object(X.jsx)(Z.a,{label:0===Object.keys(Ee).length?"Start tracking":"Edit tracking",onClick:function(){var e;ve(Object.keys(Ee)),null===$&&(e=m.patientId,D&&T.a.event({category:"Engagement",action:"Start editing health metrics",label:e}))},margin:{top:"medium"}})]}),null!==fe?Object(X.jsx)(W.a,{onEsc:function(){return ve(null)},onClickOutside:function(){return ve(null)},responsive:!1,children:Object(X.jsxs)(F.a,{width:"70vw",pad:"large",children:[Object(X.jsxs)(F.a,{direction:"row",justify:"between",children:[Object(X.jsx)(I.a,{size:"large",children:"Choose what you want to track"}),Object(X.jsx)(Z.a,{icon:Object(X.jsx)(J.a,{}),onClick:function(){return ve(null)}})]}),Object(X.jsx)(R.a,{options:["blood pressure","weight","glucose"],value:fe,onChange:function(e){ve(e.value)}}),Object(X.jsx)(ee,{animating:Te,label:"Save changes",margin:{top:"medium"},onClick:Object(d.a)(u.a.mark((function e(){return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return De(!0),console.log(fe),e.next=4,S(fe);case 4:return e.next=6,Ae();case 6:ve(null),null===$&&(t=m.patientId,D&&T.a.event({category:"Engagement",action:"Submit editing health metrics",label:t}));case 8:case"end":return e.stop()}var t}),e)})))})]})}):null,Object(X.jsxs)(F.a,{align:"center",pad:{vertical:"medium"},margin:{horizontal:"xlarge"},border:"bottom",children:[Object(X.jsx)(I.a,{textAlign:"center",margin:{vertical:"none"},children:"Dose windows"}),m?m.doseWindows.map((function(e){var t=V.DateTime.utc(2021,5,1,e.start_hour,e.start_minute),n=V.DateTime.utc(2021,5,1,e.end_hour,e.end_minute);return Object(X.jsxs)(N.a,{columns:["small","flex","flex"],align:"center",pad:{horizontal:"large"},alignContent:"center",justifyContent:"center",justify:"center",children:[Object(X.jsxs)(F.a,{direction:"row",align:"center",children:[Object(X.jsx)(I.a,{children:t.setZone("local").toLocaleString(V.DateTime.TIME_SIMPLE)}),Object(X.jsx)(U.a,{}),Object(X.jsx)(I.a,{children:n.setZone("local").toLocaleString(V.DateTime.TIME_SIMPLE)})]}),Object(X.jsx)(Z.a,{label:"edit",onClick:function(){var t;be(e),null===$&&(t=m.patientId,D&&T.a.event({category:"Engagement",action:"Start editing dose window",label:t}))},size:"small",margin:{horizontal:"none"}})]},"doseWindowContainer-".concat(e.id))})):null,Object(X.jsx)(Z.a,{label:"Add dose window",onClick:function(){var e;be({start_hour:0,start_minute:0,end_hour:0,end_minute:0}),null===$&&(e=m.patientId,D&&T.a.event({category:"Engagement",action:"Start adding dose window",label:e}))},icon:Object(X.jsx)(Y.a,{})})]}),je&&Object(X.jsx)(W.a,{onEsc:function(){return be(null)},onClickOutside:function(){return be(null)},responsive:!1,children:Object(X.jsxs)(F.a,{width:"90vw",pad:"large",children:[Object(X.jsxs)(F.a,{direction:"row",justify:"between",children:[Object(X.jsx)(I.a,{size:"large",children:"Edit dose window"}),Object(X.jsx)(Z.a,{icon:Object(X.jsx)(J.a,{}),onClick:function(){return be(null)}})]}),Object(X.jsx)(F.a,{children:Re(je)})]})}),ge&&Object(X.jsx)(W.a,{onEsc:function(){return pe(null)},onClickOutside:function(){return pe(null)},responsive:!1,children:Object(X.jsxs)(F.a,{width:"90vw",pad:"large",children:[Object(X.jsxs)(F.a,{direction:"row",justify:"between",children:[Object(X.jsx)(I.a,{size:"large",children:"Confirm delete dose window"}),Object(X.jsx)(Z.a,{icon:Object(X.jsx)(J.a,{}),onClick:function(){return pe(null)}})]}),Object(X.jsxs)(F.a,{align:"center",children:[Object(X.jsx)(I.a,{margin:{bottom:"none"},children:"You're about to delete the dose window"}),Object(X.jsxs)(F.a,{direction:"row",align:"center",margin:{bottom:"medium"},children:[Object(X.jsx)(I.a,{children:V.DateTime.utc(2021,5,1,ge.start_hour,ge.start_minute).setZone("local").toLocaleString(V.DateTime.TIME_SIMPLE)}),Object(X.jsx)(U.a,{}),Object(X.jsx)(I.a,{children:V.DateTime.utc(2021,5,1,ge.end_hour,ge.end_minute).setZone("local").toLocaleString(V.DateTime.TIME_SIMPLE)})]}),Object(X.jsx)(ee,{onClick:Object(d.a)(u.a.mark((function e(){return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return De(!0),e.next=3,k(ge.id);case 3:return e.next=5,Ae();case 5:pe(null),be(null),null===$&&(t=m.patientId,D&&T.a.event({category:"Engagement",action:"Submit deleting dose window",label:t}));case 8:case"end":return e.stop()}var t}),e)}))),label:"Confirm",animating:Te})]})]})}),Object(X.jsx)(F.a,{align:"center",pad:{vertical:"medium"},children:m?Object(X.jsxs)(X.Fragment,{children:[Object(X.jsx)(I.a,{textAlign:"center",margin:{vertical:"none"},children:"Pause / resume Coherence"}),Object(X.jsxs)(I.a,{size:"small",color:"dark-3",children:["Coherence is currently ",m.pausedService?"paused":"active","."]}),Object(X.jsx)(ee,{background:m.pausedService?{dark:!0}:null,animating:Te,style:{padding:"10px"},primary:m.pausedService,onClick:Object(d.a)(u.a.mark((function e(){return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:if(De(!0),!m.pausedService){e.next=7;break}return e.next=4,C();case 4:null===$&&(t=m.patientId,D&&T.a.event({category:"Growth",action:"Resumed service",label:t})),e.next=10;break;case 7:return e.next=9,z();case 9:null===$&&_(m.patientId);case 10:Ae();case 11:case"end":return e.stop()}var t}),e)}))),label:"".concat(m.pausedService?"Resume":"Pause"," Coherence")}),m.pausedService?Object(X.jsx)(I.a,{size:"small",color:"status-warning",textAlign:"center",children:"While Coherence is paused, we can't respond to any texts you send us, or remind you about your medications."}):null]}):null}),Object(X.jsxs)(F.a,{align:"center",pad:{vertical:"medium"},margin:{horizontal:"xlarge"},border:"top",children:[Object(X.jsx)(I.a,{textAlign:"center",margin:{vertical:"none"},children:"Need help with anything?"}),Object(X.jsx)(I.a,{size:"small",color:"dark-3",children:"Our customer service is just a text away at (650) 667-1146. Reach out any time and we'll get back to you in a few hours!"})]}),Object(X.jsx)(F.a,{align:"center",pad:{vertical:"medium"},margin:{horizontal:"xlarge"},border:"top",children:Object(X.jsx)(Z.a,{onClick:function(){c("token")},label:"Log out"})})]})},ne=n(306),ae=n(296),re=n(297),ce=n(298),ie=n(299),le=function(){var e=r.a.useState(""),t=Object(j.a)(e,2),n=t[0],a=t[1],c=r.a.useState(""),i=Object(j.a)(c,2),l=i[0],o=i[1],s=r.a.useState(""),m=Object(j.a)(s,2),g=m[0],p=m[1],x=r.a.useState(""),O=Object(j.a)(x,2),v=O[0],w=O[1],y=r.a.useState("phoneNumber"),k=Object(j.a)(y,2),z=k[0],C=k[1],S=Object(b.a)(["token"]),T=Object(j.a)(S,2),D=T[0],_=T[1],A=r.a.useState(!1),E=Object(j.a)(A,2),L=E[0],N=E[1],P=r.a.useCallback(Object(d.a)(u.a.mark((function e(){var t;return u.a.wrap((function(e){for(;;)switch(e.prev=e.next){case 0:return e.next=2,f(n,l,g);case 2:null===(t=e.sent)?N(!0):("success"===t.status&&(console.log("setting cookie"),_("token",t.token,{secure:!0})),C(t.status),N(!1));case 4:case"end":return e.stop()}}),e)}))),[g,n,l,_]),W=r.a.useCallback((function(){return"phoneNumber"===z?Object(X.jsxs)(X.Fragment,{children:[Object(X.jsx)(I.a,{textAlign:"center",size:"small",children:"Enter phone number."}),Object(X.jsx)(ne.a,{icon:Object(X.jsx)(ae.a,{}),placeholder:"(555) 555-5555",size:"small",value:n,onChange:function(e){a(e.target.value)}}),L?Object(X.jsx)(I.a,{size:"small",children:"Invalid phone number."}):null]}):"2fa"===z?Object(X.jsxs)(X.Fragment,{children:[Object(X.jsx)(I.a,{textAlign:"center",size:"small",children:"We've texted you a secret code, enter it below."}),Object(X.jsx)(ne.a,{icon:Object(X.jsx)(re.a,{}),placeholder:"123456",size:"small",value:l,onChange:function(e){o(e.target.value)}}),L?Object(X.jsx)(I.a,{size:"small",children:"Invalid secret code."}):null]}):"password"===z?Object(X.jsxs)(X.Fragment,{children:[Object(X.jsx)(I.a,{textAlign:"center",size:"small",children:"Enter password."}),Object(X.jsx)(ne.a,{icon:Object(X.jsx)(ce.a,{}),placeholder:"\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022",size:"small",value:g,onChange:function(e){p(e.target.value),w(e.target.value)},type:"password"}),L?Object(X.jsx)(I.a,{size:"small",children:"Invalid password. If you'd like us to reset it, give us a text at (650) 667-1146."}):null]}):"register"===z?Object(X.jsxs)(X.Fragment,{children:[Object(X.jsx)(I.a,{textAlign:"center",size:"small",children:"Create your password."}),Object(X.jsx)(ne.a,{icon:Object(X.jsx)(ce.a,{}),placeholder:"Enter password",size:"small",value:g,onChange:function(e){p(e.target.value)},type:"password"}),Object(X.jsx)(ne.a,{icon:Object(X.jsx)(ce.a,{}),placeholder:"Type it again",size:"small",value:v,onChange:function(e){w(e.target.value)},type:"password"}),g!==v?Object(X.jsx)(I.a,{size:"small",children:"Passwords don't match."}):null]}):void 0}),[L,z,g,v,n,l]);return D.token?Object(X.jsx)(h.a,{to:"/"}):Object(X.jsxs)(F.a,{height:"100vh",flex:"grow",background:{position:"center",dark:!1,opacity:"strong"},children:[Object(X.jsxs)(F.a,{height:"40vh",align:"center",justify:"center",pad:"large",children:[Object(X.jsx)(I.a,{children:"welcome to"}),Object(X.jsx)(M.a,{children:"coherence"})]}),Object(X.jsxs)(F.a,{height:"60vh",align:"center",justify:"between",background:{color:"brand",dark:!0},pad:"large",children:[Object(X.jsx)(I.a,{color:"white",textAlign:"center",children:"Peace of mind with your medications is just around the corner."}),Object(X.jsxs)(F.a,{children:[Object(X.jsx)(F.a,{width:"200px",margin:{bottom:"medium",top:"xsmall"},children:W()}),Object(X.jsx)(Z.a,{label:"submit",icon:Object(X.jsx)(ie.a,{}),onClick:P,disabled:g!==v})]})]})]})},oe=n(65),se=function(){return Object(X.jsx)(oe.a,{children:Object(X.jsxs)(h.d,{children:[Object(X.jsx)(h.b,{exact:!0,path:"/",render:function(){return Object(X.jsx)(te,{})}}),Object(X.jsx)(h.b,{exact:!0,path:"/login",render:function(){return Object(X.jsx)(le,{})}})]})})},ue=function(e){e&&e instanceof Function&&n.e(3).then(n.bind(null,310)).then((function(t){var n=t.getCLS,a=t.getFID,r=t.getFCP,c=t.getLCP,i=t.getTTFB;n(e),a(e),r(e),c(e),i(e)}))},de=n(300),je=n(305);i.a.render(Object(X.jsx)(r.a.StrictMode,{children:Object(X.jsx)(de.a,{children:Object(X.jsx)(je.a,{theme:{global:{colors:{brand:"#002864",text:{light:"#002864"},paragraph:{light:"#002864"},background:"#FFF"}},spinner:{container:{color:{light:"#002864",dark:"FFF"}}}},themeMode:"light",children:Object(X.jsx)(se,{})})})}),document.getElementById("root")),ue()}},[[268,1,2]]]);
//# sourceMappingURL=main.075b58d8.chunk.js.map