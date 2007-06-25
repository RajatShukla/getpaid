"""Unit test for adding a payable type to a shopping cart.
"""

import unittest
from Testing.ZopeTestCase import ZopeDocTestSuite
from utils import optionflags

from base import PloneGetPaidTestCase

def test_add_to_cart():
    """Test that payments can be processed.
    
    >>> self.setRoles(('Manager',))
    >>> id = self.portal.invokeFactory('Department', 'dept')
    >>> id = self.portal.dept.invokeFactory('Employee', 'emp')
    >>> emp = self.portal.dept.emp
    
    Set a title.
    
    >>> emp.setTitle('E. M. Ployee')
    >>> emp.Title()
    'E. M. Ployee'
    
    Set a password (note that the password cannot be read back directly.)
    
    >>> emp.setPassword('secret')
    >>> emp.getPassword()
    Traceback (most recent call last):
    ...
    AttributeError: getPassword
    
    >>> emp.setConfirmPassword('secret')
    >>> emp.getConfirmPassword()
    Traceback (most recent call last):
    ...
    AttributeError: getConfirmPassword
    
    Set roles.
    
    >>> emp.setRoles(('Reviewer',))
    >>> emp.getRoles()
    ('Reviewer',)
    """



def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(test_class=PloneGetPaidTestCase,
                             optionflags=optionflags),
        ))
