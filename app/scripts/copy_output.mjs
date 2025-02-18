import { copy } from 'fs-extra';

copy('./build', '../docs')
  .then(() => console.log('success!'))