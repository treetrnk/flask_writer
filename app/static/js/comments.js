$(document).ready(function() {

  $('input#name').parent('div.form-group').slideUp().hide();
  $('input#email').parent('div.form-group').slideUp().hide();
  $('input#subscribe').parent('div.form-group').slideUp().hide();
  $('.captcha').slideUp().hide();

  $('textarea#body').focus(function() {
    $('input#name').parent('div.form-group').slideDown().show();
    $('input#email').parent('div.form-group').slideDown().show();
    $('input#subscribe').parent('div.form-group').slideDown().show();
    $('.captcha').slideDown().show();
  });

});
