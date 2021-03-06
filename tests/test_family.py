'''
Copyright (c) 2016 Genome Research Ltd.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import unittest
from clinicalfilter.ped import Family, Person


class TestFamily(unittest.TestCase):
    """
    """
    
    def setUp(self):
        """ define a default Person object
        """
        
        ID = "fam_ID"
        
        self.family = Family(ID)
    
    def test__iter__(self):
        ''' test that __iter__() works correctly
        '''
        
        family_id, person_id, mom_id, dad_id = 'fam_ID', 'child', 'dad', 'mom',
        path, status, sex = 'child.vcf', '2', 'M'
        child = Person(family_id, person_id, dad_id, mom_id, sex, status, path)
        
        self.family.add_child(person_id, dad_id, mom_id, sex, status, path)
        self.family.set_child()
        
        # check the Family iterates by getting a list of the Family object
        members = list(self.family)
        self.assertEqual(members, [child, None, None])
    
    def test_add_father(self):
        """ test that add_father() works correctly
        """
        
        person_id = "parent_ID"
        path = "/home/parent.vcf"
        status = "1"
        sex = "1"
        dad_id = "0"
        mom_id = "0"
        
        # check that adding a male father doesn't raise an error
        self.family.add_father(person_id, dad_id, mom_id, sex, status, path)
        
        # check that adding a father for a second time is fine, but adding
        # a different father raises an error
        self.family.add_father(person_id, dad_id, mom_id, sex, status, path)
        with self.assertRaises(ValueError):
            self.family.add_father("different_ID", dad_id, mom_id, sex, status, path)
        
        # check that adding a female father raises an error
        self.setUp()
        sex = "2"
        with self.assertRaises(ValueError):
            self.family.add_father(person_id, dad_id, mom_id, sex, status, path)
        
    def test_add_mother(self):
        """ test that add_mother() works correctly
        """
        
        person_id = "parent_ID"
        path = "/home/parent.vcf"
        status = "1"
        sex = "2"
        dad_id = "0"
        mom_id = "0"
        
        # check that adding a female mother doesn't raise an error
        self.family.add_mother(person_id, dad_id, mom_id, sex, status, path)
        
        # check that adding a mother for a second time is fine, but adding
        # a different mother raises an error
        self.family.add_mother(person_id, dad_id, mom_id, sex, status, path)
        with self.assertRaises(ValueError):
            self.family.add_mother("different_ID", dad_id, mom_id, sex, status, path)
        
        # check that adding a male mother raises an error
        self.setUp()
        sex = "1"
        with self.assertRaises(ValueError):
            self.family.add_mother(person_id, dad_id, mom_id, sex, status, path)
        
    def test_add_child(self):
        """ check that add_child() works correctly
        """
        
        # check that we can add one child
        self.family.add_child("child1", 'dad', 'mom', 'male', '2', "/home/child1.vcf")
        self.assertEqual(len(self.family.children), 1)
        
        # check that adding multiple children works correctly
        self.family.add_child("child2", 'dad', 'mom', 'female', '2', "/home/child2.vcf")
        self.family.add_child("child3", 'dad', 'mom', 'male', '2', "/home/child3.vcf")
        self.assertEqual(len(self.family.children), 3)
    
    def test_set_child(self):
        """ test that set_child() works correctly
        """
        
        # add one child
        self.family.add_child("child1", 'dad', 'mom', 'male', '2', "/home/child1.vcf")
        
        # check that the child can be set correctly
        self.family.set_child()
        self.assertEqual(self.family.child, self.family.children[0])
    
        # add more children
        self.family.add_child("child2", 'dad', 'mom', 'male', '2', "/home/child2.vcf")
        self.family.add_child("child3", 'dad', 'mom', 'female', '2', "/home/child3.vcf")
        
        # check that the child can be set correctly with multiple children
        self.family.set_child()
        self.assertIn(self.family.child, self.family.children)
        
    
    def test_set_child_examined(self):
        """ test that set_child_examined() works correctly
        """
        
        # add one child
        self.family.add_child("child1", 'dad', 'mom', 'male', '2', "/home/child1.vcf")
        
        # check that the child can be set correctly, and can be set as having
        # been examined
        self.family.set_child()
        self.family.set_child_examined()
        self.assertTrue(self.family.children[0].is_analysed())
        self.assertIsNone(self.family.child)
        
        # add another child, and check that when we set the child, we now pick
        # up this child since the other one has previously been examined
        self.family.add_child("child2", 'dad', 'mom', 'female', '2', "/home/child2.vcf")
        self.family.set_child()
        self.assertEqual(self.family.child, self.family.children[1])
        
        # make sure that set_child_examined() doesn't default to None if we
        # have children left to analyse
        self.family.add_child("child3", 'dad', 'mom', 'female', '2', "/home/child3.vcf")
        self.family.set_child()
        self.family.set_child_examined()
        self.assertIsNotNone(self.family.child)
        
        # and set child = None once we have analysed all the children
        self.family.set_child()
        self.family.set_child_examined()
        self.assertIsNone(self.family.child)
