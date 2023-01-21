$( "#dialog" ).dialog({buttons: [
    {
      text: "Ok",
      click: function() {
        $( this ).dialog( "close" );
      }
    }
  ]});