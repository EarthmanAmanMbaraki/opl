// ==UserScript==
// @name         New Userscript
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  try to take over the world!
// @author       You
// @match        https://github.com/new
// @icon         data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==
// @grant       GM_xmlhttpRequest
// ==/UserScript==

(function () {
    'use strict';
    var add_btn = document.getElementById("repository_name");

    add_btn.addEventListener("change", function (event) {
        GM_xmlhttpRequest({
            method: 'GET',
            url: `https://opl.azurewebsites.net/customer/test/?name=woow&code=code`,
            onload: function (responseDetails) {
                // DO ALL RESPONSE PROCESSING HERE...
                alert(
                    "GM_xmlhttpRequest() response is:\n",
                    responseDetails.responseText.substring(0, 80) + '...'
                );
            }
        });
    });
})();