$(document).ready(function() { 
  var form = document.querySelector('#adminform'); 
  form.onsubmit = function() { 
    var about = document.querySelector('input[name=adminComment]'); 
    about.value = JSON.stringify(quill.root.innerHTML);
  }; 
  var form2 = document.querySelector('#userform'); 
  form2.onsubmit = function() { 
    var about2 = document.querySelector('input[name=userComment]'); 
    about2.value = JSON.stringify(quill.root.innerHTML);
  }; 
});
