$(document).ready(function() {

	var page_body = $('#page_body_input');
	if (page_body.val()) {
		var words = $('#page_body_input').val().match(/[^*#\s]+/g).length;
		$('#display_count').text(words+" words");
	}

	$("blockquote").addClass("blockquote");
	
	$("#page_body_input").on('keyup', function(e) {
		var words = this.value.match(/[^*$\s]+/g).length;
		$('#display_count').text(words+" words");
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
			$this.find("i.fas.fa-chevron-down").removeClass('fa-chevron-down').removeClass('.d-none').addClass('fa-chevron-up');
			div.slideDown();
		} else {
			$this.find("i.fas.fa-chevron-up").removeClass('fa-chevron-up').removeClass('.d-none').addClass('fa-chevron-down');
			div.slideUp();
		}
	});

	$(function () {
		$('[data-toggle="tooltip"]').tooltip();
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
		} else {
			$("#topNavbar").css("top","-80px");
			$("#sub-btn").css("bottom","-80px");
		}
		prevScrollpos = currentScrollPos;
	}

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
