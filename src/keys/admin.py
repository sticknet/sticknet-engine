#   Copyright © 2018-2023 Sticknet.
#
#   This source code is licensed under the GPLv3 license found in the
#   LICENSE file in the root directory of this source tree.

from stick_protocol.models import IdentityKey, SignedPreKey, PreKey, EncryptionSenderKey, DecryptionSenderKey, Party, PendingKey
from sticknet.admin_site import admin_site

admin_site.register(IdentityKey)
admin_site.register(SignedPreKey)
admin_site.register(PreKey)
admin_site.register(EncryptionSenderKey)
admin_site.register(DecryptionSenderKey)
admin_site.register(Party)
admin_site.register(PendingKey)
