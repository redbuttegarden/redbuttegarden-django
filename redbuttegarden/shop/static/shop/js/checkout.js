new PaymentiFrame({
 create: true,
 iframeId: "payment_iframe",
 settings: {
     account         : "220614998486",
     parentId        : "iframe_container",
     lang            : "en",
     cvv             : "required",
     width           : "300px",
     height          : "140px",
     showFrame       : false,
     devServer       : "https://cert.payconex.net",
     onload          : function(){ alert("The Payment iFrame has loaded") },
     payment_method  : "cc",
     css             : {
         class_label           : "width: 200px",
         id_expy_label         : "font-weight:600;font-family:Macondo;",
         id_cvv_label          : "color:#999999;"
     },
     text     : {
         number : {
             label       : "Enter Card Number",
             placeholder : "eg 4444333322221111"
         },
         cvv : {
             label       : "Enter CVV Number",
             placeholder : "eg CVV"
         },
         expy_double : {
             label         : "Enter Card Expiry Number",
             placeholder_1 : "Enter Month",
             placeholder_2 : "Enter Year"
         }
     },
     font     : {
         font_1 : {
             file   : "ProximaNova-Reg-webfont.woff",
             family : "ProximaNova"
         },
         font_2 : {
             file   : "ProximaNova-Sbold-webfont.ttf",
             family : "ProximaNova bold"
         }
     }
 }
});

$("#pay_now_button").click(function(){
 paymentiFrame.encrypt()
     .failure( function (err) {
         alert("Error: " + err.id + " -> " + err.message );
     })
     .invalidInput( function (data) {
         for ( var i = 0; i < data.invalidInputs.length; i++ ){
             alert("Error: " + data.invalidInputs[i].code + " -> " + data.invalidInputs[i].message );
         }
     })
     .success( function (res) {
         alert( "id " + res.id + " token=>" + res.eToken );
     })
 return false;
});