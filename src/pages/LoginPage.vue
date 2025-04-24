<template>

    <q-page class="row justify-center items-center">
      <div class="column q-pa-lg">
        <div class="row">
          <q-card square class="shadow-24" style="width:450px;height:540px; position: relative;">
            <!-- Toggle Button -->
            <div class="q-pa-sm text-right" style="position: absolute; top: 22px; right: 12px; z-index: 2;">
              <q-btn
                flat
                color="white"
                text-color="white"
                :label="register ? 'Login' : 'Register'"
                @click="switchTypeForm"
                class="q-mr-sm"
              >
                <q-tooltip>{{ register ? 'Back to login' : 'New user registration' }}</q-tooltip>
              </q-btn>
            </div>

            <!-- Header -->
            <q-card-section class="bg-deep-purple-7">
              <h4 class="text-h5 text-white q-my-md">{{ title }}</h4>
            </q-card-section>

            <!-- Form -->
            <q-card-section>
              <q-form @submit.prevent="submit" class="q-px-sm q-pt-xl">
                <q-input
                  ref="email"
                  square
                  clearable
                  v-model="email"
                  type="email"
                  lazy-rules
                  :rules="[required, isEmail]"
                  label="Email"
                >
                  <template v-slot:prepend><q-icon name="email" /></template>
                </q-input>

                <q-input
                  v-if="register"
                  ref="username"
                  square
                  clearable
                  v-model="username"
                  type="text"
                  lazy-rules
                  :rules="[required, short]"
                  label="Username"
                >
                  <template v-slot:prepend><q-icon name="person" /></template>
                </q-input>

                <q-input
                  ref="password"
                  square
                  clearable
                  v-model="password"
                  :type="passwordFieldType"
                  lazy-rules
                  :rules="[required, short]"
                  label="Password"
                >
                  <template v-slot:prepend><q-icon name="lock" /></template>
                  <template v-slot:append>
                    <q-icon :name="visibilityIcon" @click="switchVisibility" class="cursor-pointer" />
                  </template>
                </q-input>

                <q-input
                  v-if="register"
                  ref="repassword"
                  square
                  clearable
                  v-model="repassword"
                  :type="passwordFieldType"
                  lazy-rules
                  :rules="[required, short, diffPassword]"
                  label="Repeat password"
                >
                  <template v-slot:prepend><q-icon name="lock" /></template>
                  <template v-slot:append>
                    <q-icon :name="visibilityIcon" @click="switchVisibility" class="cursor-pointer" />
                  </template>
                </q-input>

                <q-btn
                  unelevated
                  size="lg"
                  color="secondary"
                  type="submit"
                  class="q-mt-md full-width text-white"
                  :label="btnLabel"
                />
              </q-form>
            </q-card-section>

            <!-- Optional: forgot password -->
            <q-card-section v-if="!register" class="text-center q-pa-sm">
              <p class="text-grey-6">Forgot your password?</p>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </q-page>

</template>

<script>
import { useAuthStore } from 'stores/auth'

export default {
  name: 'LoginPage',
  data () {
    return {
      title: 'Authorization',
      email: '',
      username: '',
      password: '',
      repassword: '',
      register: false,
      passwordFieldType: 'password',
      btnLabel: 'Login',
      visibility: false,
      visibilityIcon: 'visibility'
    }
  },
  setup () {
    const auth = useAuthStore()
    return { auth }
  },
  methods: {
    required (val) {
      return val && val.length > 0 || 'The field must be filled'
    },
    short (val) {
      return val && val.length > 3 || 'Value too short'
    },
    isEmail (val) {
      const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
      return emailPattern.test(val) || 'Enter a correct email'
    },
    diffPassword (val) {
      return val === this.password || 'Passwords do not match'
    },
    switchTypeForm () {
      this.register = !this.register
      this.title = this.register ? 'New User Registration' : 'Authorization'
      this.btnLabel = this.register ? 'Register' : 'Login'
    },
    switchVisibility () {
      this.visibility = !this.visibility
      this.passwordFieldType = this.visibility ? 'text' : 'password'
      this.visibilityIcon = this.visibility ? 'visibility_off' : 'visibility'
    },
    async submit () {
      let valid = true

      this.$refs.email.validate()
      this.$refs.password.validate()

      if (this.register) {
        this.$refs.username.validate()
        this.$refs.repassword.validate()
        valid = !this.$refs.email.hasError &&
                !this.$refs.username.hasError &&
                !this.$refs.password.hasError &&
                !this.$refs.repassword.hasError
      } else {
        valid = !this.$refs.email.hasError && !this.$refs.password.hasError
      }

      if (valid) {
        try {
          if (this.register) {
            await this.auth.register(this.email, this.username, this.password, this.repassword)
            this.$q.notify({ color: 'positive', message: 'Registration successful! Please login.' })
            this.switchTypeForm()
          } else {
            await this.auth.login(this.email, this.password)
            this.$router.push('home') // navigate after login
            this.$q.notify({ color: 'positive', message: 'Login successful!' })
          }
        } catch (err) {
          this.$q.notify({ type: 'negative', message: err })
        }
      }
    }
  }
}
</script>

<style scoped>
/* Add any custom styling here */
</style>
