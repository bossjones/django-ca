# -*- coding: utf-8 -*-
#
# This file is part of django-ca (https://github.com/mathiasertl/django-ca).
#
# django-ca is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# django-ca is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with django-ca.  If not,
# see <http://www.gnu.org/licenses/>.

from django.core.exceptions import ValidationError
from django.test import TestCase

from ..models import Certificate
from ..models import Watcher
from .base import DjangoCAWithCertTestCase
from .base import cert2_pubkey
from .base import cert3_pubkey


class TestWatcher(TestCase):
    def test_from_addr(self):
        mail = 'user@example.com'
        name = 'Firstname Lastname'

        w = Watcher.from_addr('%s <%s>' % (name, mail))
        self.assertEqual(w.mail, mail)
        self.assertEqual(w.name, name)

    def test_spaces(self):
        mail = 'user@example.com'
        name = 'Firstname Lastname'

        w = Watcher.from_addr('%s     <%s>' % (name, mail))
        self.assertEqual(w.mail, mail)
        self.assertEqual(w.name, name)

        w = Watcher.from_addr('%s<%s>' % (name, mail))
        self.assertEqual(w.mail, mail)
        self.assertEqual(w.name, name)

    def test_error(self):
        with self.assertRaises(ValidationError):
            Watcher.from_addr('foobar ')
        with self.assertRaises(ValidationError):
            Watcher.from_addr('foobar @')

    def test_update(self):
        mail = 'user@example.com'
        name = 'Firstname Lastname'
        newname = 'Newfirst Newlast'

        Watcher.from_addr('%s <%s>' % (name, mail))
        w = Watcher.from_addr('%s <%s>' % (newname, mail))
        self.assertEqual(w.mail, mail)
        self.assertEqual(w.name, newname)

    def test_output(self):
        mail = 'user@example.com'
        name = 'Firstname Lastname'

        w = Watcher(mail=mail)
        self.assertEqual(str(w), mail)

        w.name = name
        self.assertEqual(str(w), '%s <%s>' % (name, mail))


class CertificateTests(DjangoCAWithCertTestCase):
    def setUp(self):
        self.cert2 = self.load_cert(self.ca, cert2_pubkey)
        self.cert3 = self.load_cert(self.ca, cert3_pubkey)

    def test_revocation(self):
        # Never really happens in real life, but should still be checked
        c = Certificate(revoked=False)

        with self.assertRaises(ValueError):
            c.get_revocation()

    def test_subjectAltName(self):
        self.assertEqual(self.ca.subjectAltName(), 'DNS:ca.example.com')
        self.assertEqual(self.cert.subjectAltName(), 'DNS:cert1.example.com')
        self.assertEqual(self.cert2.subjectAltName(), 'DNS:cert2.example.com')
        # accidentally used cert2 in cn/san
        self.assertEqual(self.cert3.subjectAltName(), 'DNS:cert2.example.com')

    def test_basicConstraints(self):
        self.assertEqual(self.ca.basicConstraints(), 'critical,CA:TRUE, pathlen:1')
        self.assertEqual(self.cert.basicConstraints(), 'critical,CA:FALSE')
        self.assertEqual(self.cert2.basicConstraints(), 'critical,CA:FALSE')
        # accidentally used cert2 in cn/san
        self.assertEqual(self.cert3.basicConstraints(), 'critical,CA:FALSE')

    def test_issuerAltName(self):
        self.assertEqual(self.cert.issuerAltName(), 'DNS:ca.example.com')
        self.assertEqual(self.cert2.issuerAltName(), 'DNS:ca.example.com')
        self.assertEqual(self.cert3.issuerAltName(), 'DNS:ca.example.com')

    def test_authorityKeyIdentifier(self):
        self.assertEqual(self.cert.authorityKeyIdentifier(),
                         'keyid:6B:C8:CF:56:29:FC:00:55:DD:A5:ED:5A:55:B7:7C:65:49:AC:AD:B1\n')
        self.assertEqual(self.cert2.authorityKeyIdentifier(),
                         'keyid:6B:C8:CF:56:29:FC:00:55:DD:A5:ED:5A:55:B7:7C:65:49:AC:AD:B1\n')
        self.assertEqual(self.cert3.authorityKeyIdentifier(),
                         'keyid:6B:C8:CF:56:29:FC:00:55:DD:A5:ED:5A:55:B7:7C:65:49:AC:AD:B1\n')

    def test_nameConstraints(self):
        self.assertEqual(self.ca.nameConstraints(), '')

    def test_hpkp_pin(self):

        # get hpkp pins using
        #   openssl x509 -in cert1.pem -pubkey -noout \
        #       | openssl rsa -pubin -outform der \
        #       | openssl dgst -sha256 -binary | base64
        self.assertEqual(self.cert.hpkp_pin, '/W7D0lNdHVFrH/hzI16BPkhoojMVl5JmjEunZqXaEKI=')
        self.assertEqual(self.cert2.hpkp_pin, 'K8Kykt/NPbgrMs20gZ9vXpyBT8FQqa5QyRsEgNXQTZc=')
        self.assertEqual(self.cert3.hpkp_pin, 'wqXwnXNXwtIEXGx6j9x7Tg8zAnoiNjKbH1OKqumXCFg=')
