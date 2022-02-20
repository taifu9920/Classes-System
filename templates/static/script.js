var docCookies = {
  getItem: function (sKey) {
    return decodeURIComponent(document.cookie.replace(new RegExp("(?:(?:^|.*;)\\s*" + encodeURIComponent(sKey).replace(/[-.+*]/g, "\\$&") + "\\s*\\=\\s*([^;]*).*$)|^.*$"), "$1")) || null;
  },
  setItem: function (sKey, sValue, vEnd, sPath, sDomain, bSecure) {
    if (!sKey || /^(?:expires|max\-age|path|domain|secure)$/i.test(sKey)) { return false; }
    var sExpires = "";
    if (vEnd) {
      switch (vEnd.constructor) {
        case Number:
          sExpires = vEnd === Infinity ? "; expires=Fri, 31 Dec 9999 23:59:59 GMT" : "; max-age=" + vEnd;
          break;
        case String:
          sExpires = "; expires=" + vEnd;
          break;
        case Date:
          sExpires = "; expires=" + vEnd.toUTCString();
          break;
      }
    }
    document.cookie = encodeURIComponent(sKey) + "=" + encodeURIComponent(sValue) + sExpires + (sDomain ? "; domain=" + sDomain : "") + (sPath ? "; path=" + sPath : "") + (bSecure ? "; secure" : "");
    return true;
  },
  removeItem: function (sKey, sPath, sDomain) {
    if (!sKey || !this.hasItem(sKey)) { return false; }
    document.cookie = encodeURIComponent(sKey) + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT" + ( sDomain ? "; domain=" + sDomain : "") + ( sPath ? "; path=" + sPath : "");
    return true;
  },
  hasItem: function (sKey) {
    return (new RegExp("(?:^|;\\s*)" + encodeURIComponent(sKey).replace(/[-.+*]/g, "\\$&") + "\\s*\\=")).test(document.cookie);
  },
  keys: /* optional method: you can safely remove it! */ function () {
    var aKeys = document.cookie.replace(/((?:^|\s*;)[^\=]+)(?=;|$)|^\s*|\s*(?:\=[^;]*)?(?:\1|$)/g, "").split(/\s*(?:\=[^;]*)?;\s*/);
    for (var nIdx = 0; nIdx < aKeys.length; nIdx++) { aKeys[nIdx] = decodeURIComponent(aKeys[nIdx]); }
    return aKeys;
  }
};

function setupTimer(s,e) {
	current = document.getElementById('CurrentTime');
	var ends = document.getElementById('DurationTime');
	current.innerHTML = Sec2Time(s);
	ends.innerHTML = Sec2Time(e);
	t_s = s;
	t_e = e;
	setInterval("ClockTick();",1000);
}

function ClockTick() {
	if (t_s < t_e) {
		t_s += 1;
		current.innerHTML = Sec2Time(t_s);
	}else{
		clearInterval();
		location.reload();
	}
}

function Sec2Time(secs){
	var pad = function(num, size) { return ('000' + num).slice(size * -1); },
	hours = Math.floor(secs / 60 / 60),
	minutes = Math.floor(secs / 60) % 60,
	seconds = Math.floor(secs - minutes * 60);

	return pad(hours, 2) + ':' + pad(minutes, 2) + ':' + pad(seconds, 2);
}

function setThemeFromCookie() {
	var body = document.getElementsByTagName('body')[0];
	body.className = docCookies.getItem("theme") == "true" ? 'dark' : '';
	document.getElementById("slider").checked = docCookies.getItem("theme") == "true";
	
}

function toggleTheme() {
	docCookies.setItem("theme", !(docCookies.getItem("theme") == "true"), Infinity);
	setThemeFromCookie();
}

function CopyArea() {
	var Area = document.getElementById("CopyHere");
	window.getSelection().selectAllChildren(Area);
	document.execCommand("Copy")
	document.getElementsByClassName("Popup")[0].classList.toggle("show");
}

function push_message() {
	console.log("sub_token", localStorage.getItem('sub_token'));
	$.ajax({
		type: "POST",
		url: "/push_v1/",
		contentType: 'application/json; charset=utf-8',
		dataType:'json',
		data: JSON.stringify({'sub_token':localStorage.getItem('sub_token')}),
		success: function( data ){
			console.log("success",data);
    },
    error: function( jqXhr, textStatus, errorThrown ){
        console.log("error",errorThrown);
    }
	});
}

function Load() {
	setThemeFromCookie()
	document.getElementById("slider").addEventListener("change", toggleTheme);
	
	var Home = document.getElementById("Home");
	var Return = document.getElementById("Return");
	if (Home != null) Home.addEventListener("click", function(){window.location.href = "/";});
	if (Return != null) Return.addEventListener("click", function(){window.location.replace(document.referrer)});
	
	if ('serviceWorker' in navigator && 'PushManager' in window) {
		console.log('Service Worker and Push is supported');

		navigator.serviceWorker.register("./static/notify.js")
		.then(function(swReg) {
			console.log('Service Worker is registered', swReg);

			swRegistration = swReg;
			swRegistration.pushManager.getSubscription().then(function(subscription) {
				isSubscribed = !(subscription === null);

				if (isSubscribed) {
					console.log('User IS subscribed.');
				} else {
					console.log('User is NOT subscribed.');
					
					swRegistration.pushManager.subscribe({
						userVisibleOnly: true,
						applicationServerKey: applicationServerKey
					}).then(function(subscription) {
						console.log('User is subscribed.');

						localStorage.setItem('sub_token', JSON.stringify(subscription));
					})
					.catch(function(err) {
						console.log('Failed to subscribe the user: ', err);
					});
				}
				

			});
		})
		.catch(function(error) {
			console.error('Service Worker Error', error);
		});
} else {
	}
	
	$(".checkbox").change(function() {
		this.parentNode.childNodes[2].disabled = !this.checked
	});
	
	document.getElementById("mask").remove();
}

window.addEventListener("DOMContentLoaded", Load)