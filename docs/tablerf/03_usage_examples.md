Minimal Example
<TableRF Model="FormTest" PageSize="20">
    <HeaderRowTemplate>
        <th>Name</th>
    </HeaderRowTemplate>

    <BodyRowTemplate>
        <td>@context.Name</td>
    </BodyRowTemplate>
</TableRF>

Complete Example
<TableRF Delete=false Edit=false Model="FormTest" EditModel="typeof(FormTest)" 
         PageSize="20" AfterDelete="afterDelete" ActionText="Action"
         Title="Table Title" SubTitle="Table Subtitle" 
         ActionStyle="ActionStyle.Dropdown" ActionWidth="100" Add 
         AddButtonText="Add" AddUrl="/entry" Context="context"
         Filter="c => c.Age == filter.Age" EditUrl="/edit" 
         PageNo="2" Height="250" LazyLoad=true >

    <HeaderRowTemplate>
        <th style="width:auto" order-by="Name">Name</th>
        <th style="width:100px" order-by="Age">Age</th>
        <th>Division</th>
    </HeaderRowTemplate>

    <BodyRowTemplate>
        <td>@context.Name</td>
        <td style="text-align:center">
            <BadgeRF Text="@context.Age" BadgeClass="BadgeClass.Success" />
        </td>
        <td>@context.DivisionId</td>
    </BodyRowTemplate>

    <FooterRowTemplate>
        <td>Total</td>
        <td style="text-align:center">@context.Sum(x => x.Age)</td>
        <td style="text-align:center">@context.Select(x => x.DivisionId).Distinct().Count()</td>
    </FooterRowTemplate>

    <TitleBarAction>
        <div>
            <i class="fa-solid fa-user"></i>
        </div>
    </TitleBarAction>

    <ActionItem>
        <div>
            <i class="fa-solid fa-user"></i>
            <div>Custom Item 1</div>
        </div>
    </ActionItem>
</TableRF>
