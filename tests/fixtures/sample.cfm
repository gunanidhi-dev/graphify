<cfsetting enablecfoutputonly="true">
<!--- Sample CFML Template --->
<cfparam name="url.action" default="list">
<cfscript>
    // Variables
    variables.appName = "MyApp";
    variables.version = "1.0";
    
    // Function example
    function formatDate(required date dt) {
        return dateFormat(dt, "yyyy-mm-dd");
    }
    
    // Component usage
    user = new com.User();
    user.setName("John");
    user.setAge(25);
</cfscript>
<cfif url.action eq "list">
    <cfinvoke component="com.UserService" method="getUsers" returnvariable="users">
        <cfinvokeargument name="activeOnly">true</cfinvokeargument>
    </cfinvoke>
    
    <cfoutput>
    <ul>
    <cfloop array="#users#" index="u">
        <li>#u.getName()# - #u.getAge()#</li>
    </cfloop>
    </ul>
    </cfoutput>
<cfelseif url.action eq "edit">
    <cfset user = entityLoadByPK("User", url.id)>
    <cfif isDefined("form.save")>
        <cfset user.setName(form.name)>
        <cfset entitySave(user)>
        <cflocation url="?action=list">
    </cfif>
    
    <form method="post">
        <input type="text" name="name" value="#user.getName()#">
        <input type="submit" name="save" value="Save">
    </form>
</cfif>
<cfinclude template="footer.cfm">
</cfsetting>