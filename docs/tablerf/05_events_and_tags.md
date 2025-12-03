Events & Template Tags
Template Sections

<HeaderRowTemplate>

<BodyRowTemplate>

<FooterRowTemplate>

<ActionItem>

<TitleBarAction>

Events
OnRowClick
<TableRF OnRowClick="handleClick">
@code{
    void handleClick(object row) {
        // row contains table model data
    }
}
AfterDelete

Triggered after a row delete action.
void afterDelete(object deletedItem) {
   // custom logic
}

