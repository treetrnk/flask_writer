$(document).ready(function() {

  $('input#name').parent('div.col').parent('div.form-group').slideUp().hide();
  $('input#email').parent('div.col').parent('div.form-group').slideUp().hide();
  $('input#subscribe').parent('div.col').parent('div.form-group').slideUp().hide();

  $('textarea#body').focus(function() {
    $('input#name').parent('div.col').parent('div.form-group').slideDown().show();
    $('input#email').parent('div.col').parent('div.form-group').slideDown().show();
    $('input#subscribe').parent('div.col').parent('div.form-group').slideDown().show();
  });

});
