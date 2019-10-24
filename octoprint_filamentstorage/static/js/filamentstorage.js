/*
 * View model for OctoPrint-Filamentstorage
 *
 * Author: Walt Moorhouse
 * License: AGPLv3
 */
$(function() {
    function FilamentstorageViewModel(parameters) {
        var self = this;

        // assign the injected parameters
        self.settings = parameters[0];

        self.disconnected = ko.observable();
        self.disconnected(true);
        self.heaterPower = ko.observable();
        self.humidity = ko.observable();
        self.newMaxH = ko.observable();
        self.newMaxT = ko.observable();
        self.temp = ko.observable();
        self.w1 = ko.observable();
        self.w2 = ko.observable();
        self.w3 = ko.observable();
        self.w4 = ko.observable();
        self.errorMsg = ko.observable();

        self.setMaxH = function() {
            self.errorMsg("");
            self.ajaxRequest({"command": "set", "name": "H", "value": self.newMaxH()});
        };

        self.setMaxT = function() {
            self.errorMsg("");
            self.ajaxRequest({"command": "set", "name": "T", "value": self.newMaxT()});
        };

        self.tare1 = function() {
            self.tare(1);
        };

        self.tare2 = function() {
            self.tare(2);
        };

        self.tare3 = function() {
            self.tare(3);
        };

        self.tare4 = function() {
            self.tare(4);
        };

        self.tare = function(id) {
            self.errorMsg("");
            self.ajaxRequest({"command": "tare", "id": id});
        };

        self.connect = function() {
            self.errorMsg("");
            self.ajaxRequest({"command": "connect"});
        };

        self.onBeforeBinding = () => {
            self.errorMsg("");
            self.newMaxH(self.settings.settings.plugins.filamentstorage.maxH());
            self.newMaxT(self.settings.settings.plugins.filamentstorage.maxT());
            if (!self.disconnected()) {
                self.setMaxH();
                self.setMaxT();
            }
        };

        self.onDataUpdaterPluginMessage = (pluginIdent, message) => {
            if (pluginIdent === "filamentstorage") {
                self.disconnected(false);
                if (message.type === "error") {
                    self.errorMsg(message.data);
                } else if (message.type === "control") {
                    if (message.data === "disconnected") {
                        self.disconnected(true);
                    }
                } else if (message.type === "status") {
                    message.data.split(" ").forEach(pair => {
                        let parts = pair.split(":");
                        switch (parts[0]) {
                            case 'H':
                                self.humidity(parts[1]);
                                break;
                            case 'T':
                                self.temp(parts[1]);
                                break;
                            case 'P':
                                self.heaterPower(parts[1]);
                                break;
                            case 'S1':
                                self.w1(parts[1]);
                                break;
                            case 'S2':
                                self.w2(parts[1]);
                                break;
                            case 'S3':
                                self.w3(parts[1]);
                                break;
                            case 'S4':
                                self.w4(parts[1]);
                                break;
                        }
                    });
                }
            }
        };

        self.ajaxRequest = payload => {
            return $.ajax({
                url: API_BASEURL + "plugin/filamentstorage",
                type: "POST",
                dataType: "json",
                data: JSON.stringify(payload),
                contentType: "application/json; charset=UTF-8"
            });
        };

    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: FilamentstorageViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "settingsViewModel" ],
        // Elements to bind to, e.g. #settings_plugin_filamentstorage, #tab_plugin_filamentstorage, ...
        elements: [ "#tab_plugin_filamentstorage" ]
    });
});
