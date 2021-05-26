$(document).ready(function() { 
  $('.cancel').hide();
  $('.confirm').hide();
  //$('.delete').on('click', function(){
    //$('.delete').siblings('.cancel').show();
    //$('.delete').siblings('.confirm').show();
    //$(this).hide();
  //});
  //$('.cancel').on('click', function(){
    //$('.cancel').siblings('.confirm').hide();
    //$('.cancel').siblings('.delete').show();
    //$(this).hide();
  //});
  var form = document.querySelector('#adminform'); 
  form.onsubmit = function() { 
    var about = document.querySelector('input[name=adminMessage]'); 
    about.value = JSON.stringify(quill.root.innerHTML);
  }; 
  var form2 = document.querySelector('#userform'); 
  form2.onsubmit = function() { 
    var about2 = document.querySelector('input[name=userMessage]'); 
    about2.value = JSON.stringify(quill2.root.innerHTML);
  }; 
});
