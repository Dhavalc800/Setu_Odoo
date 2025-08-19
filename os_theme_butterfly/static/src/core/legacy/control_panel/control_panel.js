odoo.define('os_theme_butterfly.LegacyControlPanel', function (require) {
    "use strict";
    const ControlPanel = require('web.ControlPanel');
    const {patch} = require('web.utils');
    const {onMounted} = owl;

    patch(ControlPanel.prototype, 'os_theme_butterfly.LegacyControlPanel', {
        setup() {
             this._super();
            onMounted(() => this.onMounted());
        },

        onMounted() {
            var $target = $('[data-search]');
            $target.toggleClass("active", $target.find('.o_searchview_facet').length > 0);
            $target.find('.o_searchview_icon').on({
                click: function (e) {
                    $target.removeClass("active");
                }
            });
        },

        openSearch(ev) {
            var def = {active: 'active', timeout: 400, target: '[data-search]'}, attr = def;
            var $doc = $(document), $target = $(attr.target);
            var $elem = $(ev.currentTarget);
            ev.preventDefault();
            var $self = $elem, the_target = $self.data('target'),
                $self_st = $('[data-search=' + the_target + ']'),
                $self_tg = $('[data-target=' + the_target + ']');

            if (!$self_st.hasClass(attr.active)) {
                $self_tg.add($self_st).addClass(attr.active);
                $self_st.find('input').focus();
            } else {
                $self_tg.add($self_st).removeClass(attr.active);
                setTimeout(function () {
                    $self_st.find('input').val('');
                }, attr.timeout);
            }


            $doc.on({
                keyup: function (e) {
                    if (e.key === "Escape") {
                        $elem.add($target).removeClass(attr.active);
                    }
                },
            });


        }

    });
});
