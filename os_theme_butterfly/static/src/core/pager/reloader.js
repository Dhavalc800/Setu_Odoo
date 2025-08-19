/** @odoo-module **/

const {Component} = owl;

export class ViewReloader extends Component {
    _doReload() {
        const {limit, offset} = this.props;
        this.props.onUpdate({offset, limit});
    }
}

ViewReloader.template = "os_theme_butterfly.ViewReloader";
