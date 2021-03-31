function count_words() {
	var page_body = $('#page_body_input');
	var words = page_body.val().match(/[^*$\s]+/g).length;
	$('#display_count').text(words+" words");
	var matches = {}
	var patterns = [
		/beastfolk/g,
		/ elve/g,
		/-elve/g,
		/ elf/g,
		/-elf/g,
		/human/g,
		/treek/g,
		/dwarf/g,
		/dwarve/g,
		/saurian/g,
		/avian/g,
		/gnome/g
	];
	for (var i=0;i<patterns.length;i++) {
		var m = page_body.val().match(patterns[i]);
		if (m) {
			console.log(m);
			matches[m[0]] = m.length;
		}
	}
	for (var k in matches) {
		var current = $('#display_count').text();
		$('#display_count').text(k + ': ' + matches[k] + ', ' + current);
	}
}

function onSubmit(token) {
  console.log('recaptcha submit')
  //$(this).parents('form.g-recaptcha-form').submit();
}

$(document).ready(function() {

	$('.mkSelect2').select2();
	$('select[data-type="select2"]').select2();
	$('select[data-type="select2-tags"]').select2({
		tags: true
	});

  $('button.g-recaptcha').click(function(e) {
    console.log('Verifying recaptcha');
    var $this = $(this);
    e.preventDefault();
    grecaptcha.ready(function() {
      grecaptcha.execute($this.data('sitekey'), {action: 'submit'}).then(function(token) {
        $this.parents('form').prepend('<input type="hidden" name="token" value="' + token + '">');
        $this.parents('form').submit();
      });
    });
  });


	var page_body = $('#page_body_input');
	if (page_body.val()) {
		count_words();
	}

	page_body.on('keyup', function() {
		count_words();
	});
	
	$("blockquote").addClass("blockquote");
	
	$('input[type="hidden"]#timezone').each(function() {
		var $this = $(this);
    $this.val( moment.tz.guess() );
	});

  $('form').each(function() {
    if ($(this).find('.captcha').length) {
      var $this = $(this);
      var captcha = $this.find('.captcha').find('.captcha-box');
      var csrf = $this.find('#csrf_token');
      captcha.data('csrf', csrf.val());
      csrf.val('');
      $(this).submit(function(e) {
        e.preventDefault();
      });
    }
  });

  // Captcha Click ////////////////////
  $('.captcha-box').click(function() {
    var $this = $(this);
    var form = $this.parents('form');
    $this.html('<i class="captcha-spinner fas fa-circle-notch fa-spin"></i>');

    var startX,startY,x,y;
    $(".captcha-box").mouseenter(function(e) {
      var offset = $(this).offset();
      startX = e.pageX- offset.left;
      startY = e.pageY- offset.top;
      console.log('Mouse Enter ' + startX + ' ' + startY);
    });

    $(".captcha-box").mouseleave(function(e) {
      var $this = $(this);
      var offset = $(this).offset();
      var form = $this.parents('form');
      x = e.pageX- offset.left;
      y = e.pageY- offset.top;
      console.log('Mouse Leave ' + x + ' ' + y);
      if (x > startX + 3 || x < startX - 3) {
        form.find('#csrf_token').val($this.data('csrf'));
        $this.html('✔');
        form.find('button[type="submit"]').removeClass('disabled').prop('disabled', false);
        form.unbind('submit')
        console.log('HUMAN');
      } else {
        $this.html('<span class="text-danger">✘</span>');
        form.find('button[type="submit"]').addClass('disabled').prop('disabled', true);
        console.log('ROBOT!!');
      }
    });
  });

	$('.page-toggle').click(function(e) {
		e.stopPropigation;
		e.preventDefault();
		var $this = $(this);
		var target = $this.data('target');
		$('.page-list').hide();
		$('.page-toggle').removeClass('active');
		$(target).show();
		$this.addClass('active');
	});

	$("input#pub_date").on("focus", function() {
		if ($(this).val() == '') {
			var d = new Date();
			var day = d.getDate();
			if (day < 10) {
				day = '0' + day;
			}
			var month = d.getMonth() + 1;
			if (month < 10) {
				month = '0' + month;
			}
			var year = d.getFullYear();
			var hour = d.getHours();
			var minute = d.getMinutes();
			if (minute < 10) {
				minute = '0' + minute;
			}
			var seconds = d.getSeconds();
			if (seconds < 10) {
				seconds = '0' + seconds;
			}
			var date = year + '-' + month + '-' + day + ' ' + hour + ':' + minute + ':' + seconds;
			$(this).val(date);
		}
	});


	$(".toggle-tab").click(function(e) {
		e.stopPropagation();
		e.preventDefault();

		var $this = $(this);
		$(".toggle-tab").each(function() {
			$($(this).data('target')).slideUp();
			$(this).removeClass('active');
		});
		$this.addClass('active');
		$($this.data('target')).slideDown();
	});

	$("#page_title_input").on('keyup', function(e) {
		console.log("fart");
		var title = $(this).val();
		var slug_input = $("#page_slug_input")
		if ($("h2#page_title").text().startsWith("Add")) {
			slug_input.val(slugify($(this).val()));
		}
	});

	$('#versionSelect').on('change', function() {
		var $this = $(this);
		var host = window.location.hostname;
		var path = window.location.pathname;
		var path_list = path.split('/');
		if ($this.val() != 'current') {
			if (path_list[path_list.length - 2] == 'edit') {
				window.location = path + '/version/' + $this.val();
			} else {
				path_list.pop();
				window.location = path_list.join("/") + "/" + $this.val();
			}
		} else {
			if (path_list[path_list.length - 2] == 'version') {
				path_list.pop();
				path_list.pop();
				window.location = path_list.join("/");
			}
		}
	});

	$("#page_slug_input").on('blur', function(e) {
		var slug = $(this);
		slug.val( slugify(slug.val()) );
	});

	$('section, .jumbotron, footer').click(function() {
		$('.nav-menu').addClass('glyphicon-menu-hamburger');
		$('.nav-menu').removeClass('glyphicon-remove');
		$('#toggle-nav').slideUp();
	});

	$("#searchMod").on("shown.bs.modal", function() {
		$("#searchInput").focus();
	});

	$('#published').change(function() {
		if ($(this).prop("checked")) {
			$('#notify_subs').prop("checked", true);
		} else {
			$('#notify_subs').prop("checked", false);
		}
	});

	$(document).on('click', '.delete-btn', function() {
		var thisID = $(this).data('id');
		$('#confirmDelete').data('id', thisID);
		$('#deleteModal').modal('toggle');
	});

	$('#confirmDelete').click(function() {
		var thisID = $(this).data('id');
		$('#delete' + thisID).submit();
	});

	$(document).on('keydown', function(e) {
		//console.log(e.type);
		if (e.which == 37) {
			if ($("#prevPage").length != 0) {
				//console.log('prev');
				//$('#prevPage').trigger('click');
				window.location = $('#prevPage').attr('href');
			}
		} else if (e.which == 39) {
			if ($("#nextPage").length != 0) {
				//console.log('next');
				//$('#nextPage').trigger('click');
				window.location = $('#nextPage').attr('href');
			}
		}
	});

	$("#sub-btn-close").click(function() {
		$("#sub-btn-close").hide();
		$("#sub-btn").hide();
	});

	$('input#keyword').on('keyup', function(e) {
		var $this = $(this);
		var form = $this.parent().parent('form');
		form.attr('action', form.data("url") + $this.val());
	});

	$('.mkSelect2').select2({
		closeOnSelect: true
	});

	$('.datatable').DataTable({
		"lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]]
	});

	$('.datatable-desc').DataTable({
		"lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
		"order": [[ 0, "desc"]]
	});

	$('.datatable-sort3d').DataTable({
		"lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]],
		"order": [[ 2, "desc"]]
	});

	if (postType == "chapter" || postType == "post") {
		readProgress();

		$(window).on('resize', function() {
			readProgress();
		});
	}

	$(".toggled-div.hidden").slideUp();

	$(".div-toggler").click(function(e) {
		e.preventDefault()
		e.stopPropagation
		var $this = $(this);
		var div = $this.parent().find(".toggled-div");
		console.log("DIV:");
		console.log(div);
		if (div.is(":hidden")) {
			$this.find("i.fas.fa-chevron-down").removeClass('fa-chevron-down').addClass('fa-chevron-up');
			div.slideDown();
		} else {
			$this.find("i.fas.fa-chevron-up").removeClass('fa-chevron-up').addClass('fa-chevron-down');
			div.slideUp();
		}
	});

	$(function () {
		$('[data-toggle="tooltip"]').tooltip();
	})

	$(function () {
		$('.jquery-tooltip').tooltip();
	})

		/*
	$("#subForm").submit(function(e) {
		if ($honeypot.is(':checked')) {
			//$("#subBtn").prop("disabled", true);
			e.preventDefault();
			alert("No robots allowed!");
		}
	});
		 */

	var prevScrollpos = window.pageYOffset;
	window.onscroll = function() {
		var currentScrollPos = window.pageYOffset;
		if (prevScrollpos > currentScrollPos) {
			$("#topNavbar").css("top","0");
			$("#sub-btn").css("bottom","15px");
			if ($(window).scrollTop() > 100) {
				$("#scroll-top").css("right","20px");
			} 
		} else {
			$("#topNavbar").css("top","-200px");
			$("#sub-btn").css("bottom","-80px");
			$("#scroll-top").css("right","-80px");
		}
		prevScrollpos = currentScrollPos;
	}

	$('#scroll-top').click(function() {
			$("html, body").animate({
				scrollTop: 0
			}, 100);
			return false;
	});

});

function readProgress() {
	var contentPos = $(".content").position().top;
	var contentSize = $(".content").height();
	var windowSize = $(window).height();
	var max = contentPos + contentSize - windowSize - 150;
	var value = $(window).scrollTop();

	if (max > 0) {
		$("progress").attr('max', max);
		$("progress").attr('value', value);
		var percent = Math.round(value/max*100);
		$("progress").attr('data-original-title', 'Reading Progress (' + percent + '%)');

		$(document).on('scroll', function() {
			value = $(window).scrollTop();
			if (value >= max) {
				value = max;
			}
			percent = Math.round(value/max*100);
			$("progress").attr('value', value);
			$("progress").attr('data-original-title', 'Reading Progress (' + percent + '%)');
		});
	}
}
