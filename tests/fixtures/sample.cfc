component {
    
    public void function init() {
        variables.name = "";
    }
    
    public string function getName() {
        return variables.name;
    }
    
    public void function setName(required string name) {
        variables.name = arguments.name;
    }
    
    public numeric function calculate(numeric x) {
        return x * 2;
    }
    
    public boolean function isValid() {
        return len(variables.name);
    }
}