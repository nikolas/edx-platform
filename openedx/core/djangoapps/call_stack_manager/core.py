"""
Get call stacks of Model Class
in three cases-
1. QuerySet API
2. save()
3. delete()

classes:
CallStackManager -  stores all stacks in global dictionary and logs
CallStackMixin - used for Model save(), and delete() method

Functions:
capture_call_stack - global function used to store call stack

Decorators:
donottrack - mainly for the places where we know the calls. This decorator will let us not to track in specified cases

How to use-
1. Import following in the file where class to be tracked resides
    from openedx.core.djangoapps.call_stack_manager import CallStackManager, CallStackMixin
2. Override objects of default manager by writing following in any model class which you want to track-
    objects = CallStackManager()
3. For tracking Save and Delete events-
    Use mixin called "CallStackMixin"
    For ex.
        class StudentModule(CallStackMixin, models.Model):
4. Decorator is a parameterized decorator with class name/s as argument
    How to use -
    1. Import following
        import from openedx.core.djangoapps.call_stack_manager import donottrack
"""

import logging
import traceback
import re
import collections
import wrapt
import inspect
from django.db.models import Manager

log = logging.getLogger(__name__)

# list of regular expressions acting as filters
REGULAR_EXPS = [re.compile(x) for x in ['^.*python2.7.*$', '^.*<exec_function>.*$', '^.*exec_code_object.*$',
                                        '^.*edxapp/src.*$', '^.*call_stack_manager.*$']]
# Variable which decides whether to track calls in the function or not. Do it by default.
TRACK_FLAG = True

# List keeping track of Model classes not be tracked for special cases
# usually cases where we know that the function is calling Model classes.
HALT_TRACKING = []
log.info("HALT TRACKING initialized")
log.info(id(HALT_TRACKING))
# Module Level variables
# dictionary which stores call stacks.
# { "ModelClasses" : [ListOfFrames]}
# Frames - ('FilePath','LineNumber','Context')
# ex. {"<class 'courseware.models.StudentModule'>" : [[(file,line number,context),(---,---,---)],
#                                                    [(file,line number,context),(---,---,---)]]}
STACK_BOOK = collections.defaultdict(list)


def capture_call_stack(entity_name):
    """ logs customised call stacks in global dictionary `STACK_BOOK`, and logs it.

    Args:
        entity_name - Name of the model class

    """
    # holds temporary callstack
    # List with each element 4-tuple(filename, line number, function name, text)
    # filtered wrt reg exs
    temp_call_stack = [(frame[0],
                        frame[1],
                        frame[2],
                        frame[3])
                       for frame in [frames for frames in traceback.extract_stack()]
                       if not any(reg.match(frame[0]) for reg in REGULAR_EXPS)]

    def _print(frame):
        # returns in customized output
        return str('\n File ' + str(frame[0]) + ', line number ' + str(frame[1]) + ', in ' +
                   str(frame[2]) + '\n\t' + str(frame[3]))

    # get format of the log in desired way
    # Note - retaining the 4 tuple format for any additional use.
    final_call_stack = ""
    for frame in temp_call_stack:
        final_call_stack += _print(frame)

    if temp_call_stack not in STACK_BOOK[entity_name] and TRACK_FLAG \
            and not issubclass(entity_name, tuple(HALT_TRACKING[-1])):
        STACK_BOOK[entity_name].append(temp_call_stack)
        log.info("logging new call stack for %s:\n %s", entity_name, final_call_stack)


class CallStackMixin(object):
    """ A mixin class for getting call stacks when Save() and Delete() methods are called
    """

    def save(self, *args, **kwargs):
        """
        Logs before save and overrides respective model API save()
        """
        capture_call_stack(type(self))
        return super(CallStackMixin, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Logs before delete and overrides respective model API delete()
        """
        capture_call_stack(type(self))
        return super(CallStackMixin, self).delete(*args, **kwargs)


class CallStackManager(Manager):
    """ A Manager class which overrides the default Manager class for getting call stacks
    """
    def get_query_set(self):
        """overriding the default queryset API method
        """
        capture_call_stack(self.model)
        return super(CallStackManager, self).get_query_set()


def donottrack(*classes_not_to_be_tracked):
    """function decorator which deals with toggling call stack
    Args:
        classes_not_to_be_tracked: model classes where tracking is undesirable
    Returns:
        wrapped function
    """
    @wrapt.decorator
    def real_donottrack(wrapped, instance, args, kwargs):  # pylint: disable=W0613
        """takes function to be decorated and returns wrapped function

        Args:
            function - wrapped function i.e. real_donottrack
        """
        global HALT_TRACKING  # pylint: disable=W0603
        HALT_TRACKING.append(classes_not_to_be_tracked)
        HALT_TRACKING[-1] = list(set([x for sublist in HALT_TRACKING for x in sublist]))
        return_value = wrapped(*args, **kwargs)
        HALT_TRACKING.pop()
        return return_value
    return real_donottrack


@wrapt.decorator()
def trackit(wrapped, instance, args, kwargs):
    if instance is None:
        if inspect.isclass(wrapped):
            # Decorator was applied to a class.
            return wrapped(*args, **kwargs)
        else:
            # Decorator was applied to a function or staticmethod.
            capture_call_stack(wrapped.__module__ + "." + wrapped.__name__) 
            return wrapped(*args, **kwargs)
    else:
        if inspect.isclass(instance):
            # Decorator was applied to a classmethod.
            capture_call_stack(wrapped.__module__ + "." + wrapped.__name__) 
            return wrapped(*args, **kwargs)
        else:
            # Decorator was applied to an instancemethod.
            capture_call_stack(wrapped.__module__ + "." + wrapped.__name__)
            return wrapped(*args, **kwargs)