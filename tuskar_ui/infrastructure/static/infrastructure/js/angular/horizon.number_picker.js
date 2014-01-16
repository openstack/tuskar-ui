angular.module('horizonApp').directive('hrNumberPicker', function() {
  return {
    restrict: 'A',
    replace: true,
    scope: { initial_value: '=value' },
    templateUrl: 'numberpicker.html',
    link: function(scope, element, attrs) {
      input = element.find('input').first();
      angular.forEach(element[0].attributes, function(attribute) {
        input_attr = input.attr(attribute.nodeName);
        if (typeof input_attr === 'undefined' || input_attr === false) {
          input.attr(attribute.nodeName, attribute.nodeValue);
        }
      });

      scope.value = scope.initial_value;
      scope.disabledInput = (angular.isDefined(attrs.disabled)) ? true : false;

      scope.incrementValue = function() {
        if(!scope.disabledInput) {
          scope.value++;
        }
      }

      scope.decrementValue = function() {
        if(!scope.disabledInput && scope.value !== 0) {
          scope.value--;
        }
      }
    }
  };
})
