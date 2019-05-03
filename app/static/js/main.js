$(document).ready(function() {

	var page_body = $('#page_body_input');
	if (page_body.val()) {
		var words = $('#page_body_input').val().match(/[^*#\s]+/g).length;
		$('#display_count').text(words+" words");
	}
	
	$("#page_body_input").on('keyup', function(e) {
		var words = this.value.match(/[^*$\s]+/g).length;
		$('#display_count').text(words+" words");
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
		var path = window.location.pathname;
		var path_list = path.split('/');
		if ($this.val() != '') {
			if (path_list[path_list.length - 2] == 'edit') {
				window.location = path + '/version/' + $this.val();
			}
		}
	});

	$("#page_slug_input").on('blur', function(e) {
		var slug = $(this);
		slug.val( slugify(slug.val()) );
	});

	$('.nav-menu').click(function(e) {
		var $this = $(this);
		if ($this.hasClass('glyphicon-menu-hamburger')) {
			$(this).removeClass('glyphicon-menu-hamburger');
			$(this).addClass('glyphicon-remove');
			$('#toggle-nav').slideDown('fast');
		} else {
			$(this).addClass('glyphicon-menu-hamburger');
			$(this).removeClass('glyphicon-remove');
			$('#toggle-nav').slideUp('fast');
		}
	});

	$('i.dropdown').click(function(e) {
		e.preventDefault();
		var $this = $(this);
		if ($this.hasClass('glyphicon-menu-down')) {
			$this.parent('a').siblings('ul').slideDown();
			$this.removeClass('glyphicon-menu-down');
			$this.addClass('glyphicon-menu-up');
		} else {
			$this.parent('a').siblings('ul').slideUp();
			$this.removeClass('glyphicon-menu-up');
			$this.addClass('glyphicon-menu-down');
		}
	});

	$('section, .jumbotron, footer').click(function() {
		$('.nav-menu').addClass('glyphicon-menu-hamburger');
		$('.nav-menu').removeClass('glyphicon-remove');
		$('#toggle-nav').slideUp();
	});

	$("#searchMod").on("shown.bs.modal", function() {
		$("#searchInput").focus();
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

	$('.mkSelect2').select2({
		closeOnSelect: true
	});

	$('.datatable').DataTable({
		"lengthMenu": [[10, 25, 50, -1], [10, 25, 50, "All"]]
	});

	$(function () {
		$('[data-toggle="tooltip"]').tooltip();
	})

	if (postType == "chapter" || postType == "post") {
		readProgress();

		$(window).on('resize', function() {
			readProgress();
		});
	}

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
