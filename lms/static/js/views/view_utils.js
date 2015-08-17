;(function (define) {
    'use strict';
define(["jquery", "gettext", "common/js/components/views/feedback_prompt"],
    function ($, gettext, PromptView) {
        var confirmThenRunOperation;

        /**
         * Confirms with the user whether to run an operation or not, and then runs it if desired.
         */
        confirmThenRunOperation = function(title, message, actionLabel, operation, onCancelCallback) {
            return new PromptView.Warning({
                title: title,
                message: message,
                actions: {
                    primary: {
                        text: actionLabel,
                        click: function(prompt) {
                            prompt.hide();
                            operation();
                        }
                    },
                    secondary: {
                        text: gettext('Cancel'),
                        click: function(prompt) {
                            if (onCancelCallback) {
                                onCancelCallback();
                            }
                            return prompt.hide();
                        }
                    }
                }
            }).show();
        };

        return {
            'confirmThenRunOperation': confirmThenRunOperation
        };
    });
}).call(this, define || RequireJS.define);
