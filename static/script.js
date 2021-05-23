$(document).ready(function() { 
  var form = document.querySelector('#adminform'); 
  form.onsubmit = function() { 
    var about = document.querySelector('input[name=adminComment]'); 
    about.value = JSON.stringify(quill.getContents());
  }; 
  var form = document.querySelector('#userform'); 
  form.onsubmit = function() { 
    var about = document.querySelector('input[name=userComment]'); 
    about.value = JSON.stringify(quill.getContents());
  }; 
});
