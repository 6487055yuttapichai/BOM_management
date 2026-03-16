# import
import panel as pn
from .tdm_logging import logger, log_error, class_method_name


# component
class ViewTableColumn:
    #
    view_button = pn.widgets.Button(
                    name="View",
                    icon="adjustments-horizontal",
                    button_type="light",
                    width=100,
                    styles={
                        'border': '.5px solid #d9dcde',
                        'border-radius': '5px',
                        'background-color': '#f5f7fa',
                        'color': 'white',
                        'box-shadow': '1px 1px 2px rgba(0,0,0,0.3)',
                        'cursor': 'pointer'
                    }
                )

    
    def get_view_options(self, all_title_table, requirement_title_table):

        options = {}

        for col in all_title_table:
            if col in requirement_title_table:
                label = f"🔒 {col}"
            else:
                label = col

            options[label] = col   

        view_options = pn.widgets.CheckBoxGroup(
            options=options,
            value=all_title_table, 
            sizing_mode="stretch_width",
        )

        def enforce_required(event):
            current = set(event.new)
            required = set(requirement_title_table)

            if not required.issubset(current):
                view_options.value = list(current | required)

        view_options.param.watch(enforce_required, "value")

        return view_options
    
    def get_view_dropdown(self,view_options):
        view_dropdown = pn.Column(
                pn.Column(view_options, sizing_mode="stretch_width"),
                visible=False,
                styles={
                    "position": "absolute",
                    "top": "45px",
                    "right": "0px",
                    "background": "white",
                    "padding": "10px 12px",
                    "border-radius": "10px",
                    "box-shadow": "0px 12px 30px rgba(0,0,0,0.25)",
                    "z-index": "9999",
                    "width": "max-content",
                    "min-width": "200px",
                    "max-height": "400px",
                    "overflow-y": "auto",
                },
            )
        return view_dropdown
    
# HELPERS & CALLBACKS
    def toggle_dropdown(self,event,view_dropdown):
        view_dropdown.visible = not view_dropdown.visible

    def get_ordered_keys(self,view_options,title):
        selected_display = {
            col.replace("🔒 ", "")
            for col in view_options.value
        }
        ordered_keys = [
            key for key, display in title.items()
            if display in selected_display
        ]

        if not ordered_keys:
            ordered_keys = list(title.keys())

        return ordered_keys
